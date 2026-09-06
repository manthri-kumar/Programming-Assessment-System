import { useState } from "react";
import Editor from "@monaco-editor/react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000/evaluate";

const SAMPLE_CODE = {
  python: {
    reference:
      "def find_max(arr):\n    maximum = arr[0]\n    for x in arr:\n        if x > maximum:\n            maximum = x\n    return maximum\n\nn = int(input())\narr = list(map(int, input().split()))\nprint(find_max(arr))",
    student:
      "def find_max(arr):\n    maximum = arr[0]\n    for x in arr:\n        maximum = x\n    return maximum\n\nn = int(input())\narr = list(map(int, input().split()))\nprint(find_max(arr))",
    testCases: [{ input: "5\n3 7 2 9 4", expected_output: "9" }],
  },
  c: {
    reference:
      "#include <stdio.h>\n\nint findMax(int arr[], int n) {\n    int maximum = arr[0];\n    for(int i = 1; i < n; i++) {\n        if(arr[i] > maximum)\n            maximum = arr[i];\n    }\n    return maximum;\n}\n\nint main() {\n    int n;\n    scanf(\"%d\", &n);\n    int arr[100];\n    for (int i = 0; i < n; i++) {\n        scanf(\"%d\", &arr[i]);\n    }\n    printf(\"%d\\n\", findMax(arr, n));\n    return 0;\n}",
    student:
      "#include <stdio.h>\n\nint findMax(int arr[], int n) {\n    int maximum = arr[0];\n    for(int i = 1; i < n; i++) {\n        maximum = arr[i];\n    }\n    return maximum;\n}\n\nint main() {\n    int n;\n    scanf(\"%d\", &n);\n    int arr[100];\n    for (int i = 0; i < n; i++) {\n        scanf(\"%d\", &arr[i]);\n    }\n    printf(\"%d\\n\", findMax(arr, n));\n    return 0;\n}",
    testCases: [{ input: "5\n3 7 2 9 4", expected_output: "9" }],
  },
  java: {
    reference:
      "import java.util.Scanner;\n\npublic class Submission {\n    static int findMax(int[] arr) {\n        int maximum = arr[0];\n        for (int i = 1; i < arr.length; i++) {\n            if (arr[i] > maximum) {\n                maximum = arr[i];\n            }\n        }\n        return maximum;\n    }\n\n    public static void main(String[] args) {\n        Scanner scanner = new Scanner(System.in);\n        int n = scanner.nextInt();\n        int[] arr = new int[n];\n        for (int i = 0; i < n; i++) {\n            arr[i] = scanner.nextInt();\n        }\n        System.out.println(findMax(arr));\n    }\n}",
    student:
      "import java.util.Scanner;\n\npublic class Submission {\n    static int findMax(int[] arr) {\n        int maximum = arr[0];\n        for (int i = 1; i < arr.length; i++) {\n            maximum = arr[i];\n        }\n        return maximum;\n    }\n\n    public static void main(String[] args) {\n        Scanner scanner = new Scanner(System.in);\n        int n = scanner.nextInt();\n        int[] arr = new int[n];\n        for (int i = 0; i < n; i++) {\n            arr[i] = scanner.nextInt();\n        }\n        System.out.println(findMax(arr));\n    }\n}",
    testCases: [{ input: "5\n3 7 2 9 4", expected_output: "9" }],
  },
};

const LANGUAGES = [
  { id: "python", label: "Python" },
  { id: "c", label: "C" },
  { id: "java", label: "Java" },
];

const PIPELINE_STEPS = [
  "Code",
  "Preprocessing",
  "Comparison",
  "Evaluation Agent",
  "Feedback Agent",
  "Result",
];

function monacoLanguage(lang) {
  // Monaco has no dedicated "C" tokenizer; C is highlighted using the
  // C/C++ ("cpp") grammar, which covers C syntax correctly.
  if (lang === "c") return "cpp";
  return lang;
}

function statusClass(status) {
  if (status === "Correct") return "correct";
  if (status === "Incorrect") return "incorrect";
  return "partial";
}

function defineEditorTheme(monaco) {
  monaco.editor.defineTheme("ipa-dark", {
    base: "vs-dark",
    inherit: true,
    rules: [],
    colors: {
      "editor.background": "#161B22",
      "editor.foreground": "#E6EDF3",
      "editorLineNumber.foreground": "#4B5563",
      "editorLineNumber.activeForeground": "#8B98A9",
      "editorCursor.foreground": "#58A6FF",
      "editor.selectionBackground": "#264F78",
      "editor.lineHighlightBackground": "#1F263050",
    },
  });
}

function ConceptChips({ conceptScores }) {
  return (
    <div className="chip-row">
      {Object.entries(conceptScores).map(([concept, score]) => (
        <span key={concept} className={`chip ${score > 0 ? "pass" : "fail"}`}>
          {score > 0 ? "✓" : "⚠"} {concept}
        </span>
      ))}
    </div>
  );
}

function App() {
  const [language, setLanguage] = useState("python");
  const [referenceCode, setReferenceCode] = useState(SAMPLE_CODE.python.reference);
  const [studentCode, setStudentCode] = useState(SAMPLE_CODE.python.student);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleLanguageChange = (lang) => {
    setLanguage(lang);
    setReferenceCode(SAMPLE_CODE[lang].reference);
    setStudentCode(SAMPLE_CODE[lang].student);
    setResult(null);
    setError(null);
  };

  const handleResetStudent = () => {
    setStudentCode(SAMPLE_CODE[language].student);
  };

  const handleCopy = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Clipboard access can fail (permissions, insecure context) —
      // harmless to ignore for a demo copy button.
    }
  };

  const handleEvaluate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reference_code: referenceCode,
          student_code: studentCode,
          language,
          rubric: null,
          test_cases: SAMPLE_CODE[language].testCases,
        }),
      });

      if (!response.ok) {
        const errBody = await response.json();
        throw new Error(errBody.detail || "Evaluation failed.");
      }

      setResult(await response.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="app-header">
        <h1>Intelligent Programming Assessment</h1>
        <p>Multi-agent evaluation across Python, C, and Java.</p>
      </div>

      <div className="problem-bar">
        <div className="problem-title">
          Assessment: <strong>Find Maximum Element</strong>
        </div>
        <div className="lang-tabs">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.id}
              className={`lang-tab ${language === lang.id ? "active" : ""}`}
              onClick={() => handleLanguageChange(lang.id)}
            >
              {lang.label}
            </button>
          ))}
        </div>
      </div>

      <div className="pipeline">
        {PIPELINE_STEPS.map((step, i) => (
          <span key={step} style={{ display: "contents" }}>
            <span className={`pipeline-step ${result ? "done" : ""}`}>{step}</span>
            {i < PIPELINE_STEPS.length - 1 && <span className="pipeline-arrow">→</span>}
          </span>
        ))}
      </div>

      <div className="editor-workspace">
        <div className="editor-pane">
          <div className="editor-header">
            <span className="editor-header-title">REFERENCE SOLUTION</span>
            <div className="editor-actions">
              <span className="editor-badge editable">● Editable · Demo</span>
              <button className="icon-btn" onClick={() => handleCopy(referenceCode)}>
                Copy
              </button>
            </div>
          </div>
          <div className="monaco-wrap">
            <Editor
              height="100%"
              language={monacoLanguage(language)}
              value={referenceCode}
              onChange={(value) => setReferenceCode(value ?? "")}
              theme="ipa-dark"
              beforeMount={defineEditorTheme}
              options={{
                fontFamily: "'IBM Plex Mono', monospace",
                fontSize: 14,
                minimap: { enabled: false },
                wordWrap: "off",
                scrollBeyondLastLine: false,
                automaticLayout: true,
                tabSize: 4,
                padding: { top: 12 },
              }}
            />
          </div>
        </div>

        <div className="editor-pane">
          <div className="editor-header">
            <span className="editor-header-title">STUDENT SUBMISSION</span>
            <div className="editor-actions">
              <span className="editor-badge editable">● Editable</span>
              <button className="icon-btn" onClick={handleResetStudent}>
                Reset
              </button>
              <button className="icon-btn" onClick={() => handleCopy(studentCode)}>
                Copy
              </button>
            </div>
          </div>
          <div className="monaco-wrap">
            <Editor
              height="100%"
              language={monacoLanguage(language)}
              value={studentCode}
              onChange={(value) => setStudentCode(value ?? "")}
              theme="ipa-dark"
              beforeMount={defineEditorTheme}
              options={{
                fontFamily: "'IBM Plex Mono', monospace",
                fontSize: 14,
                minimap: { enabled: false },
                wordWrap: "off",
                scrollBeyondLastLine: false,
                automaticLayout: true,
                tabSize: 4,
                padding: { top: 12 },
              }}
            />
          </div>
        </div>
      </div>

      <div className="actions-row">
        <button className="evaluate-btn" onClick={handleEvaluate} disabled={loading}>
          {loading ? "Evaluating..." : "Evaluate Submission"}
        </button>
      </div>

      {error && <div className="error-banner">Error: {error}</div>}

      {result && (
        <div className="results">
          <div className="result-card">
            <div className="result-card-title">ASSESSMENT RESULT</div>
            <div className="score-row">
              <div className="score-number">{result.evaluation.score}/100</div>
              <div className={`status-pill ${statusClass(result.evaluation.status)}`}>
                {result.evaluation.status.toUpperCase()}
              </div>
            </div>
            <div className="section-title">concept_coverage</div>
            <ConceptChips conceptScores={result.evaluation.concept_scores} />
          </div>

          <div className="result-card">
            <div className="result-card-title">
              ◉ EVALUATION AGENT
              <span className="agent-status-badge">STATUS: COMPLETED</span>
            </div>
            <p><strong>{result.evaluation.status}</strong></p>
            <p>{result.evaluation.summary}</p>
            <div className="section-title" style={{ marginTop: "16px" }}>
              Concept Analysis
            </div>
            <ConceptChips conceptScores={result.evaluation.concept_scores} />
          </div>

          <div className="result-card">
            <div className="result-card-title">◉ FEEDBACK AGENT — PERSONALIZED FEEDBACK</div>
            <p>{result.feedback.summary}</p>

            <div className="feedback-sections">
              {result.feedback.strengths.length > 0 && (
                <div className="feedback-section strengths">
                  <div className="feedback-section-title">✓ Strengths</div>
                  <ul>
                    {result.feedback.strengths.map((s, i) => (
                      <li key={i}><span className="icon">✓</span>{s}</li>
                    ))}
                  </ul>
                </div>
              )}

              {result.feedback.weaknesses.length > 0 && (
                <div className="feedback-section weaknesses">
                  <div className="feedback-section-title">⚠ Needs Improvement</div>
                  <ul>
                    {result.feedback.weaknesses.map((w, i) => (
                      <li key={i}><span className="icon">⚠</span>{w}</li>
                    ))}
                  </ul>
                </div>
              )}

              {result.feedback.recommendations.length > 0 && (
                <div className="feedback-section recommendations">
                  <div className="feedback-section-title">→ Recommendations</div>
                  <ul>
                    {result.feedback.recommendations.map((r, i) => (
                      <li key={i}><span className="icon">→</span>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;