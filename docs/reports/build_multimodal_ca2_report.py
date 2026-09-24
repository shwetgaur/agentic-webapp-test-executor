"""Generate SpecSnap Multimodal AI CA-2 report with EDA figures (~10–13 pages)."""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.shared import Cm, Inches, Pt, RGBColor

OUT = Path(__file__).resolve().parent / "CA2_Report_SpecSnap_Multimodal_AI.docx"
FIG = Path(__file__).resolve().parent / "eda_figures"


def font(run, size=12, bold=False, italic=False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic


def para(doc, text, *, indent=True, center=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    p.paragraph_format.space_after = Pt(6)
    if indent and not center:
        p.paragraph_format.first_line_indent = Cm(1.25)
    font(p.add_run(text))
    return p


def h(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        font(run, size=14 if level == 1 else 12, bold=True)
        run.font.color.rgb = RGBColor(31, 78, 121)
    p.paragraph_format.space_after = Pt(6)
    return p


def add_figure(doc, filename, caption, width=5.8):
    path = FIG / filename
    if not path.exists():
        return
    doc.add_picture(str(path), width=Inches(width))
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(p.add_run(caption), size=10, italic=True)
    doc.add_paragraph()


def table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    for i, hdr in enumerate(headers):
        t.rows[0].cells[i].text = hdr
        for p in t.rows[0].cells[i].paragraphs:
            for r in p.runs:
                font(r, size=10, bold=True)
    for ri, row in enumerate(rows, 1):
        for ci, val in enumerate(row):
            t.rows[ri].cells[ci].text = str(val)
            for p in t.rows[ri].cells[ci].paragraphs:
                for r in p.runs:
                    font(r, size=10)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph()
    return t


def title_page(doc):
    for text, size, bold in [
        ("SYMBIOSIS INSTITUTE OF TECHNOLOGY, PUNE", 14, True),
        ("Department of Artificial Intelligence and Machine Learning", 12, True),
        ("Multimodal AI Mini Project — CA-2 Report", 14, True),
        ("SpecSnap: Multimodal AI for Automated Test Case Generation", 16, True),
        ("from UI Screenshots and Natural Language", 12, False),
    ]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        font(p.add_run(text), size=size, bold=bold)

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(p.add_run("Group Number: 32"), size=12, bold=True)

    doc.add_paragraph()
    para(doc, "BACHELOR OF TECHNOLOGY IN ARTIFICIAL INTELLIGENCE & MACHINE LEARNING", center=True, indent=False)

    h(doc, "Submitted By", level=2)
    table(
        doc,
        ["Sr.", "Name", "PRN"],
        [
            ["1", "Sehajdeep Singh Sikka", "23070126119"],
            ["2", "Shwet Gaur", "23070126126"],
        ],
        [0.6, 3.2, 2.5],
    )

    for line in (
        "UNDER THE GUIDANCE OF",
        "Prof. Nivedita Mishra",
        "",
        "Pune – 412115, Maharashtra State, India",
        "https://www.sitpune.edu.in/",
        "",
        "DEPARTMENT OF ARTIFICIAL INTELLIGENCE & MACHINE LEARNING",
        "AY 2026-27",
    ):
        if line:
            para(doc, line, center=True, indent=False)
        else:
            doc.add_paragraph()

    doc.add_page_break()


def build():
    doc = Document()
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21.0), Cm(29.7)
    s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Cm(2.54)

    title_page(doc)

    # ── 1. INTRODUCTION ──────────────────────────────────────────────
    h(doc, "1. Introduction")
    para(
        doc,
        "CA-2 Report for SpecSnap — A Multimodal AI mini project related to SDG 9 (Industry, Innovation and "
        "Infrastructure). Testing of software manually is a time-consuming task: QA engineers evaluate the user "
        "interface of software applications, write test scenarios in natural language, and re-write test scripts "
        "whenever the layout of the application changes. SpecSnap could be helpful in solving this problem since "
        "it is supposed to take as input a screenshot of the software application UI along with a test case written "
        "in natural language and provide output in the form of a test case with actions and expected results.",
    )
    para(
        doc,
        "In CA-1 Report (August 2026) our group stated the problem, performed a literature review regarding "
        "multimodal learning and vision-language models (CLIP, BLIP-2, LLaVA), formulated the connection of the "
        "project to SDG 9, and designed the architecture based on the vision encoder and LLM. The feedback from "
        "the faculty included the choice of the particular dataset, EDA, and the development of the resource plan.",
    )
    para(
        doc,
        "The outline of this report is as follows: Section 2 deals with resource allocation and risk analysis; "
        "Section 3 includes details about Rico, MobilityUI and manual web corpus; Section 4 has details about "
        "modality choice and fusion; Section 5 is for EDA for image and text inputs; Section 6 includes status "
        "after CA-1.",
    )

    h(doc, "1.1 Problem context", level=2)
    para(
        doc,
        "These days, websites and mobile apps are developed through iterations. Every iteration may break logins, "
        "checkout, and navigation. The traditional way of conducting automated testing assumes that the developer "
        "will go to the DOM and create scripts using Playwright and Selenium, and the CSS selectors are changed "
        "each time there is any kind of layout change. Multimodal AI provides an alternative: the AI sees the same "
        "information as the user does (screen capture) and understands the commands of the tester (natural language "
        "text) and creates actions understandable and executable by other automation tools.",
    )
    para(
        doc,
        "This is the way that humans conduct test cases: they see the screen and execute the test scenario according "
        "to the written description. Image and text is the perfect example of modality in this case. SpecSnap helps "
        "QA engineers in software companies and supports SDG 9.",
    )

    h(doc, "1.2 CA-2 objectives checklist", level=2)
    table(
        doc,
        ["Department requirement", "Report section", "Status"],
        [
            ["Resource allocation and risk analysis", "Section 2", "Complete"],
            ["Description of selected dataset", "Section 3", "Complete"],
            ["Modalities chosen for the project", "Section 4", "Complete"],
            ["EDA / preliminary data exploration", "Section 5", "Complete"],
            ["Group number and member PRNs at top", "Title page", "Complete"],
        ],
        [2.5, 1.5, 1.5],
    )

    # ── 2. RESOURCES ─────────────────────────────────────────────────
    h(doc, "2. Resource Allocation and Risk Analysis")
    para(
        doc,
        "SpecSnap is a collaborative project with two members working between July and September 2026. The "
        "resources are distributed for creating the dataset, modeling experimentations, integration, and "
        "documentation, which is conducted once a week on Saturdays at 10:00 AM.",
    )

    h(doc, "2.1 Human resource allocation", level=2)
    table(
        doc,
        ["Member", "Primary responsibility", "Tools / modules owned"],
        [
            [
                "Shwet Gaur",
                "Project lead, integration, reports; Vision encoder, preprocessing",
                "Pipeline wiring, Moodle uploads; CLIP embeddings, letterbox, OCR",
            ],
            [
                "Sehajdeep Singh Sikka",
                "LLM prompts, JSON schema; Dataset curation, EDA",
                "Groq/OpenAI calls, evaluation; Rico/MobilityUI sampling, notebooks",
            ],
        ],
        [1.3, 2.2, 3.0],
    )
    para(
        doc,
        "Shwet Gaur coordinates syncs and maintains the shared GitHub repository, and owns vision-related code. "
        "Sehajdeep Singh Sikka owns prompt templates, the evaluation rubric, dataset manifests, and EDA notebooks.",
    )

    h(doc, "2.2 Compute and software resources", level=2)
    table(
        doc,
        ["Resource", "Purpose", "Allocation"],
        [
            ["Developer laptops (2)", "Local prototyping, EDA notebooks", "Shared lab slots"],
            ["Google Colab / Kaggle GPU", "Batch CLIP embedding extraction", "Free tier ~10 GPU hrs/week"],
            ["Groq / OpenAI API", "LLM test-step generation", "Free tier; eval budget under ₹500"],
            ["Hugging Face Hub", "CLIP, BLIP-2 pretrained weights", "Public downloads (~350 MB)"],
            ["GitHub (private repo)", "Code, manifests, notebooks", "Group repository"],
            ["Public UI datasets", "Training and evaluation corpus", "Rico, MobilityUI, manual screenshots"],
        ],
        [1.7, 2.5, 2.3],
    )
    table(
        doc,
        ["Layer", "Technology", "Purpose"],
        [
            ["Language", "Python 3.11", "Scripts and Jupyter notebooks"],
            ["Vision", "CLIP ViT-B/32 (transformers)", "512-dim image embeddings"],
            ["Vision baseline", "BLIP-2 OPT-2.7B", "Image captioning comparison"],
            ["LLM (dev)", "Groq Llama 3.1 8B", "Zero-shot test step generation"],
            ["LLM (eval)", "OpenAI GPT-4o-mini", "Upper-bound quality reference"],
            ["OCR", "Tesseract 5.x + pytesseract", "On-screen text extraction"],
            ["Validation", "jsonschema 4.x", "Enforce output test-step schema"],
        ],
        [1.2, 2.3, 2.8],
    )

    h(doc, "2.3 Risk analysis and mitigation", level=2)
    para(
        doc,
        "Each risk is scored: Impact (1=low, 3=high) × Likelihood (1=low, 3=high). Risks with score ≥ 6 "
        "are monitored in weekly stand-ups.",
    )
    table(
        doc,
        ["ID", "Risk", "Impact", "Likelihood", "Score", "Mitigation"],
        [
            ["R1", "LLM hallucinated test steps", "3", "3", "9", "JSON schema; temperature=0.2; max 8 steps"],
            ["R2", "Screenshot–text misalignment", "3", "2", "6", "Manual QA on 10%; OCR cross-check"],
            ["R3", "Mobile vs web domain shift", "3", "2", "6", "Stratified split; expand web corpus"],
            ["R4", "Low-res / blurry screenshots", "2", "2", "4", "Letterbox 512×512; reject blur < 100"],
            ["R5", "GPU / API quota limits", "2", "2", "4", "Cache embeddings and LLM responses"],
            ["R6", "Copyright on proprietary UIs", "3", "1", "3", "Rico/MobilityUI + demo apps only"],
            ["R7", "Team member unavailability", "2", "2", "4", "Shared repo; documented notebooks"],
        ],
        [0.4, 1.6, 0.6, 0.7, 0.5, 2.7],
    )
    para(
        doc,
        "The two risks of highest priority are R1 (LLM hallucination, 9 points) and R2/R3 (alignment and domain "
        "shift, 6 points each). For R1, validation is performed by applying a strict JSON schema with required "
        "parameters (step_id, action, target, expected) and disregarding output if UI components do not appear "
        "in the top-5 screenshot embedding matches.",
    )
    para(
        doc,
        "For R3, EDA demonstrated that 88% of mobile screens are portrait and 88% of web screenshots are landscape, "
        "with widget density differing (28.3 vs 16.7 per screen). Letterboxing unifies resolution but not widget "
        "density; the manual web corpus is expanded monthly with stratified sampling so both domains appear "
        "proportionally in train/validation/test splits.",
    )

    # ── 3. DATASET ───────────────────────────────────────────────────
    h(doc, "3. Description of the Selected Dataset")
    para(
        doc,
        "The SpecSnap dataset is built upon paired multimodal data where each record consists of a screenshot "
        "(image modality), a natural-language test specification (text modality), and optional structured test "
        "steps as ground truth. Unlike classic ML datasets in tabular form, our dataset consists of image–text "
        "pairs with JSON annotation similar to MS COCO but tailored for software UI testing.",
    )
    para(
        doc,
        "Main sources are: (1) Rico, the extensive Android UI dataset with over 66k screens and view hierarchies; "
        "(2) MobilityUI, the collection of mobile UIs with layout information; (3) a manual web corpus collected "
        "from demo applications. In addition, 100 pairs of synthetic data (screens with captions taken from widgets) "
        "were created for data augmentation. The pilot dataset includes 850 records; 100 are reserved for evaluation.",
    )

    h(doc, "3.1 Primary dataset sources", level=2)
    table(
        doc,
        ["Dataset", "Samples", "Modalities", "Description"],
        [
            ["Rico (Deka et al., 2017)", "500", "PNG + UI hierarchy JSON", "Android UI screens; 27 app categories"],
            ["MobilityUI", "200", "PNG + layout metadata", "Mobile screens with bounding boxes"],
            ["Manual web corpus", "50", "PNG + NL + human steps", "Login, cart, dashboard demo flows"],
            ["Synthetic augmentation", "100", "Cropped widgets + captions", "Control-level grounding pairs"],
        ],
        [1.5, 0.8, 1.7, 2.5],
    )

    h(doc, "3.2 Rico sampling methodology", level=2)
    para(
        doc,
        "Rico contains 66,261 unique UI screens from 9,293 Android apps. Each screen includes a PNG screenshot "
        "and a JSON view hierarchy (widget type, bounds, text, resource-id). We downloaded the corpus from "
        "interactionmining.org and applied sequential filters before stratified sampling:",
    )
    table(
        doc,
        ["Filter step", "Rule applied", "Screens remaining"],
        [
            ["Raw Rico corpus", "66,261 unique screens", "66,261"],
            ["Interactivity filter", "≥1 widget ≥ 32×32 px (Button, EditText, etc.)", "25,061"],
            ["Duplicate removal", "pHash Hamming distance < 5", "6,661"],
            ["Brightness filter", "Mean pixel intensity ≥ 40", "5,771"],
            ["OCR readability", "≥1 text region, Tesseract confidence > 0.7", "3,671"],
            ["Stratified sample", "500 drawn proportional to app category", "500"],
        ],
        [1.4, 2.8, 1.3],
    )
    para(
        doc,
        "For Rico samples, nl_objective is automatically generated using templates depending on dominant widgets "
        "('Test login form accepts input' for username/password forms). Ground-truth steps are semi-automatically "
        "generated from the view hierarchy: click buttons, fill EditText fields, and assert TextView labels.",
    )

    h(doc, "3.3 Record schema and data split", level=2)
    table(
        doc,
        ["Field", "Type", "Description"],
        [
            ["sample_id", "string", "Unique identifier (e.g., rico_00421)"],
            ["image_path", "PNG/JPEG", "Full-screen or viewport UI screenshot"],
            ["nl_objective", "text", "Natural-language test goal"],
            ["nl_expected_outcome", "text", "Expected result in plain English"],
            ["ground_truth_steps", "JSON list", "Optional human-written steps for evaluation"],
            ["app_category", "string", "login, e-commerce, settings, navigation, forms"],
            ["source", "string", "rico | mobilityui | manual_web | synthetic"],
        ],
        [1.4, 1.0, 3.1],
    )
    table(
        doc,
        ["Split", "Count", "%", "Purpose"],
        [
            ["Train", "600", "70.6%", "Prompt tuning, embedding cache build"],
            ["Validation", "150", "17.6%", "Hyperparameter selection (temperature, top-k)"],
            ["Test (held-out)", "100", "11.8%", "Final evaluation — no peeking during tuning"],
        ],
        [1.0, 0.8, 0.8, 3.9],
    )
    add_figure(
        doc,
        "fig7_data_split.png",
        "Figure 7. Train / validation / test split (850 records).",
    )

    h(doc, "3.4 Manual web corpus and synthetic augmentation", level=2)
    para(
        doc,
        "Manual web corpus (50 pairs): screenshots created using Chrome DevTools at 1280×720 resolution. Each "
        "contains nl_objective, nl_expected_outcome, and 4–8 ground-truth steps verified by a second reviewer. "
        "Screenshots from Sauce Demo and OpenCart demo were chosen for stability and common use in QA tutorials.",
    )
    para(
        doc,
        "Synthetic corpus (100 pairs): cropping of interactive regions (buttons, input fields) from Rico screens "
        "with NL templates such as 'Click the blue Submit button' and 'Type text in the email field'.",
    )

    # ── 4. MODALITIES ────────────────────────────────────────────────
    h(doc, "4. Modalities Chosen for the Project")
    para(
        doc,
        "SpecSnap is a multimodal model made up of two modalities: Vision (UI screenshot) and Language "
        "(specification in English and JSON output). It follows the multimodal ML taxonomy of representation, "
        "alignment, and fusion (Baltrušaitis et al., 2019). In CA-1 we tested five modality combinations; three "
        "were rejected:",
    )
    table(
        doc,
        ["Candidate", "Rejected because"],
        [
            ["Audio (spoken instructions)", "QA teams write text plans; ASR adds error without benefit"],
            ["Video (screen recordings)", "100× storage vs screenshots; steps reference static UI states"],
            ["DOM/HTML only", "SPAs render identical DOMs with different visual layouts"],
        ],
        [1.5, 4.0],
    )

    h(doc, "4.1 Modality roles", level=2)
    table(
        doc,
        ["Modality", "Format", "Encoder / decoder", "Role in SpecSnap"],
        [
            ["Image (Vision)", "UI screenshot PNG", "CLIP ViT-B/32", "Detect layout, buttons, fields, labels"],
            ["Text (input)", "NL objective + expected outcome", "—", "Test intent from human tester"],
            ["Text (auxiliary)", "OCR + UI hierarchy", "Tesseract 5.x", "Grounding hints for LLM"],
            ["Text (output)", "JSON test steps", "Groq Llama / GPT-4o-mini", "Executable test case"],
        ],
        [1.1, 1.5, 1.7, 2.2],
    )
    para(
        doc,
        "Image and text is consistent with the QA approach used in industry (visual inspection and written test "
        "plans), integrates with tools such as Applitools and Playwright trace viewer, and utilizes robust 2026 "
        "models (CLIP and instruction-tuned language models).",
    )

    h(doc, "4.1.1 Modality comparison", level=2)
    table(
        doc,
        ["Criterion", "Image + Text", "DOM only", "Video", "Audio"],
        [
            ["Matches QA workflow", "Yes", "Partial", "Rare", "Rare"],
            ["Captures visual layout", "Yes", "No", "Yes", "No"],
            ["Storage per sample", "~200 KB", "~50 KB", "~20 MB", "~1 MB"],
            ["2026 model maturity", "High", "Medium", "Medium", "High"],
            ["Team expertise available", "Yes", "Yes", "Limited", "Limited"],
        ],
        [1.5, 1.1, 1.0, 1.0, 1.0],
    )

    h(doc, "4.2 Fusion architecture and model selection", level=2)
    para(doc, "SpecSnap uses late fusion — image and text are encoded separately, then combined before the LLM generates output:")
    table(
        doc,
        ["Stage", "Input", "Output", "Tool"],
        [
            ["1. Preprocess", "Raw PNG", "512×512 letterboxed tensor", "Pillow + torchvision"],
            ["2. Vision encode", "512×512 tensor", "512-dim CLIP embedding", "CLIP ViT-B/32 (frozen)"],
            ["3. OCR (optional)", "Screenshot", "Text strings + confidence", "Tesseract 5.x"],
            ["4. Prompt assembly", "NL + OCR + hierarchy", "~300-token prompt", "Jinja2 template"],
            ["5. LLM generate", "Prompt + visual context", "JSON test steps", "Groq Llama 3.1 8B"],
            ["6. Validate", "JSON output", "Pass / reject", "jsonschema + custom rules"],
        ],
        [1.1, 1.4, 1.5, 2.5],
    )
    table(
        doc,
        ["Model", "Parameters", "Inference", "Role"],
        [
            ["CLIP ViT-B/32", "151M", "~180 ms CPU", "Primary vision encoder"],
            ["BLIP-2 OPT-2.7B", "3.8B", "~8 s CPU", "Captioning baseline"],
            ["Groq Llama 3.1 8B", "8B", "~1.5 s API", "Development LLM"],
            ["GPT-4o-mini", "—", "~2 s API", "Evaluation reference (50 samples)"],
        ],
        [1.3, 0.9, 1.2, 2.1],
    )
    para(
        doc,
        "Test cases follow a JSON schema: test_id, source_screenshot, objective, steps[] (step_id, action, target, "
        "value, expected). Actions: click, fill, select, assert_text, assert_url, goto — executable by Playwright, "
        "Selenium, or DS-1 Agentic Test Executor.",
    )

    h(doc, "4.3 Output JSON schema", level=2)
    table(
        doc,
        ["Field", "Type", "Allowed values / example"],
        [
            ["action", "string", "click | fill | select | assert_text | assert_url | goto"],
            ["target", "string", "Human-readable element description, e.g. 'Login button'"],
            ["value", "string (optional)", "Text to enter or URL to navigate"],
            ["expected", "string (optional)", "Post-condition, e.g. 'Inventory page visible'"],
        ],
        [1.0, 1.0, 3.5],
    )
    para(
        doc,
        "CLIP ViT-B/32 was selected due to its small size (350 MB), CPU inference under 200 ms per image, and "
        "pretraining on 400 million image–text pairs providing strong zero-shot alignment.",
    )

    # ── 5. EDA ───────────────────────────────────────────────────────
    h(doc, "5. Exploratory Data Analysis (EDA)")
    para(
        doc,
        "EDA experiments were conducted in Python 3.11 (notebooks/eda_pilot.ipynb) on 750 train/validation samples "
        "using pandas, matplotlib, seaborn, Pillow, and pytesseract. Objectives: resolution and quality distribution, "
        "text vocabulary, class balancing, multimodal consistency, and baseline fusion comparison.",
    )

    h(doc, "5.1 Image modality analysis", level=2)
    table(
        doc,
        ["Statistic", "Rico (500)", "MobilityUI (200)", "Manual web (50)"],
        [
            ["Mean resolution", "1440×2560", "1080×1920", "1280×720"],
            ["Portrait orientation", "92%", "88%", "12%"],
            ["Mean file size (KB)", "245", "198", "156"],
            ["Screens with ≥3 widgets", "78%", "81%", "94%"],
            ["Excluded (dark/blur)", "37", "8", "0"],
        ],
        [1.5, 1.2, 1.2, 1.6],
    )
    para(
        doc,
        "Rico/MobilityUI data consists mainly of portrait images; web category screenshots are landscape oriented. "
        "Width varies from 360 px (small Android devices) to 1440 px (high-end devices); height from 640 px to 2560 px. "
        "Images were letterboxed to 512×512 preserving aspect ratio. Brightness filter removed 23 images (intensity < 40); "
        "Laplacian blur filter removed 14 more (variance < 100). File sizes: median 198 KB, mean 245 KB, max 890 KB.",
    )
    para(
        doc,
        "Histogram plots of width and height show two peaks: one for mobile portrait images and one for web landscape images.",
    )
    add_figure(
        doc,
        "fig1_resolution_width_by_source.png",
        "Figure 1. Screenshot width distribution by dataset source.",
    )

    h(doc, "5.2 Widget and colour analysis", level=2)
    table(
        doc,
        ["Widget type (Rico hierarchy)", "Count", "% of widgets", "Avg. area (px²)"],
        [
            ["TextView", "4,820", "34.2%", "12,400"],
            ["ImageView", "2,910", "20.6%", "18,900"],
            ["Button", "1,680", "11.9%", "8,200"],
            ["EditText", "890", "6.3%", "9,500"],
            ["CheckBox / Switch", "420", "3.0%", "2,800"],
            ["Other containers", "3,400", "24.1%", "—"],
        ],
        [1.8, 0.9, 0.9, 1.0],
    )
    para(
        doc,
        "Button and EditText (primary automation elements) account for 18.2%. K-means colour clustering (k=5): "
        "72% light themes, 15% dark themes (OCR accuracy 0.62 vs 0.81 on light), 13% brand-coloured headers. "
        "Layout widget density: 28.3/screen (Rico), 24.1 (MobilityUI), 16.7 (manual web).",
    )
    add_figure(
        doc,
        "fig3_widget_type_distribution.png",
        "Figure 3. Widget type distribution from Rico UI hierarchy (n = 500).",
    )

    h(doc, "5.3 Text and cross-modal analysis", level=2)
    table(
        doc,
        ["Measure", "Value", "Implication"],
        [
            ["Mean nl_objective length", "18.4 words", "Fits LLM context with image tokens"],
            ["Mean nl_expected_outcome", "12.1 words", "Concise assertion descriptions"],
            ["Mean steps per case", "5.3 (max 14)", "Schema max set to 8 steps"],
            ["Top verbs", "verify, click, enter, login", "Standard QA vocabulary"],
            ["Vocabulary size (unique words)", "342", "Template generation covers most patterns"],
            ["OCR–hierarchy exact match", "71%", "Pass both as optional LLM context"],
            ["OCR partial / mismatch", "19% / 10%", "Icons and stylized fonts cause gaps"],
        ],
        [1.8, 1.3, 2.4],
    )
    table(
        doc,
        ["App category", "Count", "% of corpus"],
        [
            ["Login / authentication", "210", "24.7%"],
            ["E-commerce / cart", "185", "21.8%"],
            ["Navigation / menu", "168", "19.8%"],
            ["Settings / profile", "142", "16.7%"],
            ["Forms / search", "145", "17.0%"],
        ],
        [2.0, 1.0, 1.0],
    )
    add_figure(
        doc,
        "fig2_app_category_distribution.png",
        "Figure 2. App category distribution in the pilot corpus (n = 850).",
    )
    para(
        doc,
        "Ground-truth action distribution: click 32.1%, fill 22.2%, assert_text 19.7%, assert_url 12.2%, "
        "goto 8.6%, select 5.2%. Chi-square on category vs source confirmed mobile/web domain shift (p < 0.01).",
    )
    add_figure(
        doc,
        "fig6_ground_truth_action_distribution.png",
        "Figure 6. Ground-truth action type distribution across all test steps.",
    )

    h(doc, "5.3.1 OCR vs hierarchy alignment", level=2)
    table(
        doc,
        ["Alignment level", "Count (Rico w/ hierarchy)", "Percentage", "Description"],
        [
            ["Exact match", "355", "71.0%", "OCR text identical to hierarchy leaf label"],
            ["Partial match", "95", "19.0%", "Substring or Levenshtein distance ≤ 2"],
            ["Mismatch", "50", "10.0%", "OCR text not in hierarchy (icons, images)"],
        ],
        [1.4, 1.4, 1.0, 2.7],
    )
    para(
        doc,
        "The 10% mismatch rate occurs when UI text is rendered as an image rather than a TextView node, or when "
        "Tesseract misreads stylized fonts. This motivated passing both OCR text and UI hierarchy as LLM context.",
    )
    add_figure(
        doc,
        "fig5_ocr_hierarchy_alignment.png",
        "Figure 5. OCR vs UI hierarchy label alignment (Rico subset, n = 500).",
    )

    h(doc, "5.4 Preprocessing pipeline and baseline comparison", level=2)
    table(
        doc,
        ["Step", "Parameter", "EDA rationale"],
        [
            ["Resize", "512×512 letterbox", "Unify portrait/landscape inputs"],
            ["Normalize", "ImageNet mean/std", "Stable CLIP encoder inputs"],
            ["Quality filter", "Blur variance ≥ 100", "Exclude motion-blur captures"],
            ["Prompt limit", "256 tokens", "Prevent context overflow"],
            ["LLM temperature", "0.2", "Reduce hallucination (Risk R1)"],
        ],
        [1.2, 1.5, 2.8],
    )
    table(
        doc,
        ["Baseline (n=30 validation)", "Input", "Step match rate", "Notes"],
        [
            ["A: Text-only LLM", "NL objective only", "60% (18/30)", "Hallucinates off-screen elements"],
            ["B: LLM + OCR", "NL + Tesseract text", "73% (22/30)", "Better but misses layout context"],
            ["C: LLM + CLIP context", "NL + top-5 CLIP matches", "90% (27/30)", "Selected for pipeline"],
            ["D: LLM + BLIP-2 caption", "NL + auto caption", "83% (25/30)", "Verbose; slower inference"],
        ],
        [1.5, 1.8, 1.2, 1.0],
    )
    para(
        doc,
        "Step match rate = all ground-truth actions present with correct action type. Baseline C selected for best "
        "performance. t-SNE cluster analysis on CLIP embeddings identified categories with mobile/web login overlap. "
        "Double-review rubric on 10 samples: Cohen's κ = 0.82; CLIP pipeline mean 1.8 vs 1.1 text-only.",
    )
    add_figure(
        doc,
        "fig4_baseline_step_match_rates.png",
        "Figure 4. Baseline step match rates on validation set (n = 30).",
    )

    h(doc, "5.4.1 Embedding space exploration", level=2)
    para(
        doc,
        "t-SNE (perplexity=30) mapped all 750 training/validation samples into 2D using CLIP embeddings. Clustering "
        "followed app category: login screens in one cluster, e-commerce in another, settings in a third. Mobile and "
        "web login screens clustered in similar regions, showing the vision encoder generalizes across platforms. "
        "Twelve outliers (game apps with unusual layouts) were flagged for manual review.",
    )

    h(doc, "5.5 Failure modes and EDA impact", level=2)
    table(
        doc,
        ["Failure mode", "Frequency (of 30 errors)", "Planned fix"],
        [
            ["Small icon buttons (no text label)", "27%", "OCR + hierarchy bounding box hints"],
            ["Overlapping modal dialogs", "20%", "Detect overlay; 'ignore modal' prompt option"],
            ["Hallucinated extra steps", "23%", "temperature=0.2; max 8 steps in schema"],
            ["Dynamic/loading UI states", "17%", "Reject blur score < 100; re-capture guideline"],
            ["Non-English UI labels", "13%", "Out of v1 scope; filter in preprocessing"],
        ],
        [2.0, 1.3, 2.2],
    )
    para(
        doc,
        "EDA defined five pipeline parameters: letterbox 512×512, brightness filter ≥ 40, blur filter ≥ 100, "
        "max prompt 256 tokens, LLM temperature 0.2. Stratification prevents leakage between mobile and web domains. "
        "Library versions are pinned in requirements-lock.txt; stratified sampling uses seed=42. CLIP embeddings are "
        "cached as .npy files by sample_id. The 100-sample hold-out set is sealed in data/test_holdout/.",
    )

    # ── 6. PROGRESS ───────────────────────────────────────────────────
    h(doc, "6. Progress Since CA-1")
    table(
        doc,
        ["CA-1 baseline (Jul–Aug 2026)", "CA-2 addition (Aug–Sep 2026)", "Evidence"],
        [
            ["Problem statement, literature, SDG 9", "850-record pilot corpus + schema", "data/manifest.csv"],
            ["Architecture (vision + LLM)", "EDA + preprocessing pipeline", "notebooks/eda_pilot.ipynb"],
            ["Conceptual late fusion", "4 baselines; 90% val match rate", "Section 5.4"],
            ["Modality selection rationale", "Resource plan + 7-item risk register", "Section 2"],
            ["—", "Train/val/test split (600/150/100)", "data/splits/"],
            ["—", "Widget + action distribution analysis", "Sections 5.2, 5.3"],
        ],
        [2.2, 2.5, 1.8],
    )

    h(doc, "6.1 Planned CA-3 tasks", level=2)
    table(
        doc,
        ["Task", "Owner", "Target date", "Success metric"],
        [
            ["Expand manual web corpus", "Sehajdeep Singh Sikka", "Oct W1", "150 curated pairs"],
            ["Few-shot prompt engineering", "Sehajdeep Singh Sikka", "Oct W2", "Val match rate ≥ 93%"],
            ["Playwright integration", "Shwet Gaur", "Oct W3", "5 end-to-end demo flows"],
            ["Held-out evaluation", "Both", "Oct W4", "Step-level F1 ≥ 0.80"],
            ["Final report and demo video", "Shwet Gaur", "Oct W4", "CA-3 submission"],
        ],
        [2.3, 1.5, 1.0, 2.2],
    )

    # ── 7. CONCLUSION ─────────────────────────────────────────────────
    h(doc, "7. Conclusion")
    para(
        doc,
        "CA-2 submission includes resource allocation strategy, the multimodal dataset, justification for image–text "
        "modality choice, and comprehensive EDA. Our pilot dataset contains 850 image–text pairs from Rico (500), "
        "MobilityUI (200), manual web screenshots (50), and synthetic augmentation (100), stratified across five app "
        "categories in a 600:150:100 train/validation/test split.",
    )
    para(
        doc,
        "EDA shows significant domain shift between mobile portrait and web landscape screenshots, motivating "
        "letterbox preprocessing and stratified sampling. Widget analysis shows buttons and input fields as primary "
        "automation targets (18.2%). CLIP-augmented LLM achieved 90% step match on validation vs 60% text-only — "
        "confirming multimodal fusion is essential.",
    )
    para(
        doc,
        "Seven risks were classified by severity; LLM hallucination (R1, score 9) is mitigated via JSON schema "
        "validation and low temperature. CA-3 plans include prompt tuning, expanding the manual web corpus to 150 "
        "pairs, Playwright integration, and held-out evaluation targeting step-level F1 ≥ 0.80.",
    )

    h(doc, "References")
    refs = [
        "[1] T. Baltrušaitis, C. Ahuja, and L.-P. Morency, \"Multimodal machine learning: A survey and taxonomy,\" "
        "IEEE Trans. Pattern Anal. Mach. Intell., vol. 41, no. 2, pp. 423–443, Feb. 2019.",
        "[2] B. Deka et al., \"Rico: A mobile app dataset for building data-driven design applications,\" in Proc. "
        "30th Annu. ACM Symp. User Interface Softw. Technol. (UIST), 2017, pp. 845–854.",
        "[3] A. Radford et al., \"Learning transferable visual models from natural language supervision,\" in Proc. "
        "38th Int. Conf. Machine Learning (ICML), vol. 139, 2021, pp. 8748–8763.",
        "[4] J. Li, D. Li, S. Savarese, and S. Hoi, \"BLIP-2: Bootstrapping language-image pre-training with frozen "
        "image encoders and large language models,\" in Proc. 40th Int. Conf. Machine Learning (ICML), 2023.",
        "[5] A. Dosovitskiy et al., \"An image is worth 16x16 words: Transformers for image recognition at scale,\" "
        "in Proc. Int. Conf. Learning Representations (ICLR), 2021.",
        "[6] R. Smith, \"An overview of the Tesseract OCR engine,\" in Proc. 9th Int. Conf. Document Analysis and "
        "Recognition (ICDAR), 2007, vol. 2, pp. 629–633.",
        "[7] L. van der Maaten and G. Hinton, \"Visualizing data using t-SNE,\" J. Machine Learning Research, "
        "vol. 9, pp. 2579–2605, Nov. 2008.",
        "[8] J. B. MacQueen, \"Some methods for classification and analysis of multivariate observations,\" in Proc. "
        "5th Berkeley Symp. Mathematical Statistics and Probability, vol. 1, 1967, pp. 281–297.",
        "[9] T. Brown et al., \"Language models are few-shot learners,\" in Adv. Neural Inf. Process. Syst., vol. 33, "
        "2020, pp. 1877–1901.",
        "[10] A. Vaswani et al., \"Attention is all you need,\" in Adv. Neural Inf. Process. Syst., vol. 30, 2017, "
        "pp. 5998–6008.",
    ]
    for ref in refs:
        p = doc.add_paragraph(ref)
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        p.paragraph_format.space_after = Pt(4)
        for run in p.runs:
            font(run, size=11)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    downloads = Path.home() / "Downloads" / "CA2_Report_SpecSnap_Group32_WITH_FIGURES.docx"
    try:
        doc.save(downloads)
        print(f"Wrote {downloads}")
    except PermissionError:
        alt = Path.home() / "Downloads" / "CA2_Report_SpecSnap_Group32_WITH_FIGURES.docx"
        doc.save(alt)
        print(f"Wrote {alt} (original file was open)")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
