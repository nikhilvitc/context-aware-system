import {
  Document,
  Packer,
  Paragraph,
  TextRun,
  Table,
  TableRow,
  TableCell,
  WidthType,
  HeadingLevel,
  BorderStyle,
  ShadingType,
  AlignmentType,
} from "docx";
import fs from "fs";

const PAGE = 12240;
const MARGIN = 720;
const W = PAGE - 2 * MARGIN;
const borders = {
  top: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
  bottom: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
  left: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
  right: { style: BorderStyle.SINGLE, size: 4, color: "999999" },
};

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 80 },
    children: [
      new TextRun({
        text,
        size: opts.size || 20,
        bold: !!opts.bold,
        italics: !!opts.italics,
        font: "Calibri",
      }),
    ],
  });
}

function cell(text, width, opts = {}) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: opts.shade
      ? { type: ShadingType.CLEAR, fill: opts.shade }
      : undefined,
    children: [
      new Paragraph({
        spacing: { after: 40, before: 40 },
        children: [
          new TextRun({
            text: text || "",
            size: opts.size || 17,
            bold: !!opts.bold,
            font: "Calibri",
            color: opts.color || "000000",
          }),
        ],
      }),
    ],
  });
}

function headerRow(cols, widths) {
  return new TableRow({
    children: cols.map((c, i) =>
      cell(c, widths[i], { bold: true, shade: "1F4E79", size: 16, color: "FFFFFF" })
    ),
  });
}

function dataRow(cols, widths) {
  return new TableRow({
    children: cols.map((c, i) => {
      const shade =
        i === 3
          ? c === "New"
            ? "C6EFCE"
            : c === "Improved"
              ? "BDD7EE"
              : c === "Same"
                ? "FFF2CC"
                : "F2F2F2"
          : i === 2
            ? "EAF2F8"
            : undefined;
      return cell(c, widths[i], { shade, size: 16 });
    }),
  });
}

function sectionTable(rows) {
  // # | Q | Existing | Proposed | Status | Evidence
  const widths = [500, 2200, 2600, 3200, 1100, 2040];
  return new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      headerRow(
        [
          "#",
          "Questionnaire",
          "Existing system (SLA)",
          "Proposed system",
          "Status",
          "Evidence / metric",
        ],
        widths
      ),
      ...rows.map((r) => dataRow(r, widths)),
    ],
  });
}

function kTable(rows) {
  const widths = [700, 3200, 2400, 1600, 2200, 2140];
  return new Table({
    width: { size: W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      headerRow(
        [
          "#",
          "Proposed contribution",
          "Module/stage affected",
          "Status vs SLA",
          "Primary metric",
          "Expected / observed gain",
        ],
        widths
      ),
      ...rows.map((r) => dataRow(r, widths)),
    ],
  });
}

const h = (t) =>
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text: t, bold: true, size: 26, font: "Calibri", color: "1F4E79" })],
  });

const doc = new Document({
  styles: {
    default: { document: { styles: [{ id: "Normal", run: { font: "Calibri", size: 20 } }] } },
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: PAGE, height: 15840 },
          margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN },
        },
      },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 120 },
          children: [
            new TextRun({
              text: "Contribution Assessment Questionnaire: Base Paper (SLA) vs Proposed System",
              bold: true,
              size: 28,
              font: "Calibri",
              color: "1F4E79",
            }),
          ],
        }),
        p(
          'Base paper: "Separate, Locate, and Align: Determine Context Relation of Scene Text From Multiple Perspectives in TextVQA" (SLA: TSS + SCP + VA on T5; extension of SaL). Proposed system: Tap2Explain / RhymeTextVQA — children\'s nursery-rhyme domain adaptation of SLA-style TSS+SCP+VA with interactive tap-to-explain UI.',
          { size: 18 }
        ),
        p(
          "Status legend: Same | Improved | New | Weaker | Not addressed. Accuracy on TextVQA/ST-VQA vs published SLA can be improved later; domain results and system novelty are filled at full strength.",
          { size: 17, italics: true }
        ),

        h("A. Problem and task definition"),
        sectionTable([
          [
            "A1",
            "What exact TextVQA problem is the system trying to solve?",
            "Treating all OCR tokens as one sentence introduces false context relations between unrelated scene text.",
            "Same core problem, specialised to children's rhyme picture books: verse lines, titles and illustration labels must not be falsely joined; relations must respect rhyme layout (couplets/lines) and picture–text links.",
            "Improved",
            "One-sentence problem statement + rhyme-page failure cases",
          ],
          [
            "A2",
            "What is the final user-facing task?",
            "Answer a natural-language question about text in an image (TextVQA, ST-VQA).",
            "Dual task: (1) RhymeTextVQA — answer child-friendly questions about rhyme pages; (2) Tap2Explain UI — child taps a word or illustration and receives a rhyme-aware explanation grounded in TSS/SCP/VA neighbours.",
            "New",
            "Demo: tap 'sheep' / word 'Baa' → kid explanation; QA examples in data/exports",
          ],
          [
            "A3",
            "Is the answer generated, selected from OCR, or both?",
            "Generative decoding with T5 (answers may copy OCR tokens).",
            "Closed-vocab answer classification over short rhyme answers (title, object labels, relation hints) plus generative Gemini explanations for the interactive UI (with offline fallback).",
            "Improved",
            "Answer-type breakdown: text / object / relation; UI explanation samples",
          ],
          [
            "A4",
            "What counts as a 'context relation' between text regions?",
            "Semantic, spatial and visual (colour) relatedness of OCR regions.",
            "Same three perspectives, rhyme-specialised: TSS = same verse-line / lexical adjacency; SCP = 2D proximity on picture-book page; VA = colour/appearance affinity of token crops; plus text–object links for illustrations.",
            "Improved",
            "Formal definition in research/sla/modules.py + API relation scores",
          ],
          [
            "A5",
            "Which datasets and domains are in scope?",
            "TextVQA, ST-VQA (natural scene images).",
            "New domain: RhymeTextVQA — public-domain Mother Goose nursery rhymes, synthesised illustrated pages, OCR tokens, objects, and TextVQA-style QAs (60 pages, 1,405 QAs). Real uploaded rhyme PDFs/images also supported in the app.",
            "New",
            "Dataset list: data/rhyme_textvqa.db, data/exports/{train,val,test}.jsonl",
          ],
          [
            "A6",
            "What failure of SLA motivates the proposal?",
            "To be identified by the proposer.",
            "SLA targets open-world street/shop scene text and returns only VQA answers. It does not teach children English via rhyme books, does not support tap-on-illustration (monkey on tree), and does not expose TSS/SCP/VA as an interactive learning UI. Scene-text assumptions also mismatch verse layout.",
            "New",
            "Concrete failure: SLA cannot explain a tapped nursery-rhyme illustration to a child",
          ],
          [
            "A7",
            "Do both systems solve the same primary problem? If not, what is the narrower/broader scope?",
            "Context-relation modelling for TextVQA.",
            "Narrower domain (children's rhymes) but broader product scope: relation modelling + interactive educational explanation for text and pictures. Same TSS/SCP/VA scientific core.",
            "Improved",
            "Explicit scope statement in research/NOVELTY.md",
          ],
        ]),

        h("B. Inputs, OCR and feature extraction"),
        sectionTable([
          [
            "B1",
            "Which OCR system is used, and is it fixed or trainable?",
            "External OCR (e.g., Microsoft-OCR / Rosetta); not trained jointly.",
            "EasyOCR (CPU) for uploads; native PDF text-layer when available; layout ground-truth OCR for RhymeTextVQA page builder. OCR fixed (not jointly trained).",
            "Same",
            "OCR engine: EasyOCR + PyMuPDF text layer; version pinned in requirements",
          ],
          [
            "B2",
            "What features represent each OCR token?",
            "Word embedding + visual region features + bounding-box layout.",
            "Token embedding + normalised bbox + local RGB crop features; line_index for verse structure; optional object labels as extra tokens.",
            "Improved",
            "Feature schema in research/sla/data.py",
          ],
          [
            "B3",
            "What visual features of the whole image are used?",
            "Object/region visual features; paper analyses effect of visual features.",
            "Per-token colour patches for VA; illustration object boxes (label, category, relation_hint) for picture-tap questions; no full FRCNN object detector yet on real photos.",
            "Improved",
            "Object schema in SQLite objects table; ablation planned for detector upgrade",
          ],
          [
            "B4",
            "How robust is the system to OCR errors?",
            "Analysed in paper (OCR-error experiments).",
            "Supports dual path: clean text-layer vs EasyOCR; synthetic pages use GT boxes for controlled training. Full noisy-OCR stress test scheduled as next experiment.",
            "Not addressed",
            "Accuracy under noisy vs clean OCR (to be filled after stress test)",
          ],
          [
            "B5",
            "Does the proposal add new input information unavailable to SLA?",
            "No beyond text, box, region and RGB colour histograms.",
            "Yes: verse line_index, rhyme title/full text, illustration object labels + relation hints, interactive tap coordinates, kids-mode explanation prompts.",
            "New",
            "Ablation with/without objects & line_index (next)",
          ],
          [
            "B6",
            "Is reading order assumed or learned?",
            "Reading order not trusted; relations via TSS/SCP.",
            "Same philosophy: 2D SCP + line-aware TSS; no forced left-to-right sentence concat for context.",
            "Same",
            "Order-perturbation test (planned)",
          ],
          [
            "B7",
            "Can recognition errors be separated from reasoning errors?",
            "Partially (OCR robustness analysis).",
            "Partially: source tag (ocr vs text_layer) in UI; answer_type taxonomy (text/object/relation) for error analysis.",
            "Improved",
            "Error taxonomy by answer_type in exports",
          ],
        ]),

        h("C. Semantic separation (TSS module)"),
        sectionTable([
          [
            "C1",
            "How is the boundary between unrelated text groups modelled?",
            "Learnable <context> token after each OCR region.",
            "Same <context> interleaving, plus rhyme specialisation: same-line tokens get a soft adjacency prior so couplets stay linked while title chrome separates.",
            "Improved",
            "Mechanism: research/sla/modules.py TSSModule",
          ],
          [
            "C2",
            "What attention mask is used?",
            "Context-aware mask letting context tokens attend to visual and positional info.",
            "Context tokens fused with visual/position cues; line-equality prior modulates context embeddings before multimodal fusion.",
            "Improved",
            "Mask/prior description in modules.py",
          ],
          [
            "C3",
            "Is grouping supervised or implicitly learned?",
            "Implicit, via answer loss.",
            "Primarily implicit via answer CE loss; line_index provides weak structural prior (not hard supervision).",
            "Improved",
            "Supervision: answer CE + line prior",
          ],
          [
            "C4",
            "Can the grouping be visualised or evaluated directly?",
            "Qualitative attention visualisation only.",
            "Yes in product: UI draws TSS/SCP/VA scored neighbours and relation chips on tap; research ablations toggle TSS on/off.",
            "New",
            "UI relation graph + ablation reports in research/checkpoints/",
          ],
          [
            "C5",
            "What changes in the proposal to semantic separation, and why better?",
            "-",
            "Verse-line prior + educational exposure of TSS scores; better match to rhyme structure than street-scene grouping alone.",
            "Improved",
            "Ablation vs TSS on RhymeTextVQA",
          ],
        ]),

        h("D. Spatial relations (SCP module)"),
        sectionTable([
          [
            "D1",
            "How are positions of text regions encoded?",
            "Regions mapped to grid; pairwise spatial distances; relative-position embeddings in attention.",
            "Pairwise 2D centre distances binned into learnable SCP attention bias (circle-style distance), applied to OCR self-attention; also used at inference for neighbour ranking.",
            "Same",
            "Formula in research/sla/modules.py SCPModule",
          ],
          [
            "D2",
            "Is direction (left/above) encoded or only distance?",
            "Circle-based distance (direction-agnostic largely).",
            "Distance-based SCP (same as SLA spirit); direction can be added later via quadrant bins.",
            "Same",
            "Direction-sensitive rhyme questions (planned)",
          ],
          [
            "D3",
            "How does the system handle rotated/curved/perspective text?",
            "Bounding-box based; not explicitly handled.",
            "Bounding-box based; picture books are mostly upright — acceptable for target domain.",
            "Same",
            "Not a primary rhyme-book failure mode",
          ],
          [
            "D4",
            "Is grid granularity a sensitive hyperparameter?",
            "Reported grid choices.",
            "num_bins=32 distance embedding; sensitivity sweep planned.",
            "Same",
            "Sensitivity curve (planned)",
          ],
          [
            "D5",
            "What new spatial-reasoning mechanism does the proposal contribute?",
            "-",
            "SCP scores exposed in interactive UI; spatial links between OCR tokens and illustration objects for picture-tap learning.",
            "New",
            "Ablation vs SCP + UI SCP edges",
          ],
        ]),

        h("E. Visual alignment (VA module)"),
        sectionTable([
          [
            "E1",
            "What visual cue relates text regions?",
            "RGB colour distributions compared with KL divergence.",
            "Same idea: RGB histograms / colour affinity of token crops; inference also uses OpenCV hist correlation when available.",
            "Same",
            "Cue definition in VAModule + backend/services/relations.py",
          ],
          [
            "E2",
            "How are channel-specific relations fused?",
            "Gating mechanism over R, G, B representations.",
            "RGB gating inspired by SLA (sigmoid gates over channel similarities) in VAModule.",
            "Same",
            "Fusion in research/sla/modules.py",
          ],
          [
            "E3",
            "Are cues beyond colour used (font, stroke, texture, background)?",
            "No, colour only.",
            "Colour primary; title strip vs body colour regions in synthesised pages act as layout-colour cues. Font/stroke not yet explicit.",
            "Improved",
            "Title/body colour separation on built pages",
          ],
          [
            "E4",
            "How sensitive is VA to lighting/colour shifts?",
            "Colour-granularity analysis reported.",
            "Not yet stress-tested; scheduled after real-book ingestion.",
            "Not addressed",
            "Colour-jitter robustness (planned)",
          ],
          [
            "E5",
            "What new visual-relation capability does the proposal add?",
            "-",
            "VA scores shown to learners; visual grouping used together with object taps (illustration affinity to nearby words).",
            "New",
            "Ablation vs VA + UI VA chips",
          ],
        ]),

        h("F. Reasoning, fusion and answer generation"),
        sectionTable([
          [
            "F1",
            "What backbone performs multimodal reasoning?",
            "T5 (Base/Large) encoder-decoder.",
            "Lightweight multimodal encoder with question–OCR–object cross-attention and TSS/SCP/VA biases (CPU-trainable). UI explanations via Gemini LMM with local fallback. Upgrade path to T5/LaTr-style backbone documented.",
            "Improved",
            "Backbone: research/sla/model.py (d=256); Gemini for explain",
          ],
          [
            "F2",
            "How are question, OCR and visual tokens fused?",
            "Concatenated into T5 encoder with added relation biases.",
            "Question, OCR (optionally TSS-expanded), and object tokens fused; SCP/VA biases on OCR attention; question-conditioned pooling into answer classifier.",
            "Improved",
            "Fusion schema in model.py forward()",
          ],
          [
            "F3",
            "Does the system use scene-text-specific pre-training?",
            "No extra pre-training tasks/data (but pretrained T5).",
            "No large IDL-style pretraining; trains from RhymeTextVQA domain data (efficient for project scale).",
            "Same",
            "Pre-training statement: none beyond embeddings init",
          ],
          [
            "F4",
            "Does the proposal use LLMs/LMMs, retrieval, or external knowledge?",
            "No.",
            "Yes for UX: Gemini generates child-friendly explanations grounded in selected token + TSS/SCP/VA context; offline template fallback if API fails.",
            "New",
            "Module: backend/services/explain.py",
          ],
          [
            "F5",
            "Can the system explain which text regions supported the answer?",
            "Not explicitly.",
            "Yes: tap UI highlights selected token, neighbour boxes, relation graph and per-edge SCP/TSS/VA scores; explanation cites rhyme context.",
            "New",
            "Evidence-grounding via UI + relation JSON",
          ],
          [
            "F6",
            "How are multi-hop or numeric/comparative questions handled?",
            "Implicitly by T5.",
            "Covered via relation/object QAs (e.g., where is the monkey; three bags). Deeper numeric multi-hop left for later T5 upgrade.",
            "Improved",
            "Accuracy by answer_type in exports",
          ],
        ]),

        h("G. Efficiency and deployment"),
        sectionTable([
          [
            "G1",
            "How many extra parameters are added?",
            "Small overhead; trade-off reported.",
            "Compact CPU model (embedding + few attention layers + TSS/SCP/VA); far smaller than T5-Large SLA for the rhyme demo.",
            "Improved",
            "Param count via checkpoint size ~4MB full_best.pt",
          ],
          [
            "G2",
            "What is inference latency and memory?",
            "Not a primary focus.",
            "Interactive localhost app: FastAPI + React; OCR once per page; tap context is near-instant; Gemini explain ~3s timeout then fallback.",
            "Improved",
            "ms/tap local; Gemini timeout env KIDS_GEMINI_TIMEOUT_SEC=3",
          ],
          [
            "G3",
            "Does the proposal reduce training cost or data needs?",
            "-",
            "Yes for the target domain: trains on ~1.4k rhyme QAs on CPU in minutes, no IDL 64M pretraining required for the educational demo.",
            "Improved",
            "GPU-hours ≈ 0 (CPU); dataset size in summary.json",
          ],
          [
            "G4",
            "Can it run on edge/mobile devices?",
            "Not addressed.",
            "CPU-friendly path demonstrated (EasyOCR CPU + small model). Mobile packaging not yet done.",
            "Improved",
            "Laptop CPU demo live at localhost:5174",
          ],
        ]),

        h("H. Results and contribution evidence"),
        sectionTable([
          [
            "H1",
            "What are headline results?",
            "TextVQA val 64.91 / test 64.58 (SLA-Large); ST-VQA val 64.49, ANLS 0.728.",
            "RhymeTextVQA (our domain): Full TSS+SCP+VA val VQA acc 70.0%, test 75.2% (ANLS val 0.714 / test 0.767). Not claiming TextVQA SOTA vs SLA yet — same-setting TextVQA comparison is future work.",
            "New",
            "research/checkpoints/ablation_summary.json; full_best.pt",
          ],
          [
            "H2",
            "What is the gain of each module?",
            "All three: +4.99 TextVQA, +4.26 ST-VQA; +0.55 over SaL.",
            "On RhymeTextVQA, full model beats no-module baseline on test (75.2% vs 72.3%). Earlier ablations showed VA/SCP helping val. Larger matched ablations after T5 upgrade.",
            "Improved",
            "Per-module ablation_summary.json",
          ],
          [
            "H3",
            "Which proposed component gives the largest gain?",
            "-",
            "Domain specialisation (rhyme dataset + verse priors) + full TSS/SCP/VA fusion; product-wise the tap-to-explain + object grounding is the largest unique gain vs SLA.",
            "New",
            "Ablation table + demo comparison",
          ],
          [
            "H4",
            "Does the proposal generalise to unseen datasets?",
            "Not reported.",
            "App already ingests real rhyme PDFs/images (e.g., Baa Baa Black Sheep scan). Formal OCR-VQA/DocVQA transfer not yet reported.",
            "Improved",
            "Real upload demo; cross-dataset later",
          ],
          [
            "H5",
            "Strongest evidence of unique contribution beyond SLA?",
            "-",
            "(1) New RhymeTextVQA domain + dataset pipeline; (2) interactive TSS/SCP/VA-grounded kid explanations for text AND pictures; (3) ≥70% domain VQA with full modules. TextVQA matched bake-off pending.",
            "New",
            "NOVELTY.md + live system + checkpoints",
          ],
        ]),

        h("J. Evaluation fairness and experimental design"),
        sectionTable([
          [
            "J1",
            "Are both systems evaluated on the same splits?",
            "TextVQA / ST-VQA standard splits.",
            "Currently evaluated on RhymeTextVQA stratified QA splits (80/10/10). Fair SLA comparison will use official TextVQA/ST-VQA splits when backbone is upgraded.",
            "Not addressed",
            "Split confirmation: data/exports/summary.json",
          ],
          [
            "J2",
            "Same OCR tokens for both systems?",
            "Paper-specified OCR.",
            "Within our system, train/val/test share the same OCR/GT pipeline. Cross-paper OCR equivalence pending matched reimplementation.",
            "Not addressed",
            "OCR equivalence statement for future bake-off",
          ],
          [
            "J3",
            "Same backbone size and pretrained weights?",
            "T5-Base / T5-Large.",
            "Not yet matched (lightweight encoder vs T5). Planned: re-run with T5-base + TSS/SCP/VA for fair SLA comparison.",
            "Weaker",
            "Matched T5 configuration (planned)",
          ],
          [
            "J4",
            "Same training data?",
            "Single and joint TextVQA+ST-VQA settings.",
            "Trains on RhymeTextVQA only (domain focus). Optional joint fine-tune later.",
            "New",
            "Training-data: public-domain rhymes only",
          ],
          [
            "J5",
            "Are results repeated over multiple seeds?",
            "Single-run figures typical.",
            "Primary seed 42 reported; multi-seed mean±std planned.",
            "Same",
            "Mean ± std (planned)",
          ],
          [
            "J6",
            "Is compute reported equally?",
            "Parameters reported.",
            "CPU training time, checkpoint size, and latency notes included; FLOPs table planned.",
            "Improved",
            "Cost notes in G1–G3",
          ],
          [
            "J7",
            "Comparisons against recent strong baselines?",
            "PreSTU, LaTr, etc.",
            "Internal none vs full ablation on RhymeTextVQA; LaTr/SLA reimplementation comparison planned.",
            "Not addressed",
            "Baseline list for next milestone",
          ],
          [
            "J8",
            "Does the proposal outperform SLA under matched conditions?",
            "-",
            "Not yet on TextVQA/ST-VQA under matched T5 settings. On RhymeTextVQA domain task, full modules reach ≥70% and beat no-module baseline on test. Matched SLA bake-off is the accuracy-improvement track.",
            "Not addressed",
            "Statistical comparison after T5 matched run",
          ],
        ]),

        h("K. Summary of proposed unique contributions"),
        kTable([
          [
            "K1",
            "RhymeTextVQA: public-domain children's rhyme TextVQA dataset (pages, OCR, objects, QAs) with reproducible build pipeline",
            "Data / domain",
            "New",
            "Dataset size & split quality",
            "60 pages, 1,405 QAs; train/val/test JSONL",
          ],
          [
            "K2",
            "SLA-style TSS + SCP + VA specialised to verse lines and picture-book layout",
            "TSS / SCP / VA",
            "Improved",
            "VQA acc / ANLS on RhymeTextVQA",
            "Full: val 70.0%, test 75.2%",
          ],
          [
            "K3",
            "Interactive Tap2Explain kids mode: tap word OR illustration → TSS/SCP/VA neighbours + child explanation",
            "Fusion + UX / explainability",
            "New",
            "Usability + grounding",
            "Live demo localhost:5174; relation chips per edge",
          ],
          [
            "K4",
            "Object-aware rhyme QAs and picture-tap explanations (e.g., monkey/sheep with relation hints)",
            "Inputs + answer types",
            "New",
            "Object/relation QA accuracy",
            "answer_type ∈ {text,object,relation}",
          ],
          [
            "K5",
            "CPU-efficient educational deployment with Gemini LMM explanations + offline fallback (no hard dependency on cloud for demo)",
            "Efficiency / deployment",
            "New",
            "Latency & reliability",
            "CPU train/infer; explain fallback always returns text",
          ],
        ]),

        new Paragraph({ spacing: { before: 300 }, children: [] }),
        p(
          "Note: Rows marked Not addressed / Weaker are intentionally honest about the TextVQA matched bake-off and T5 parity, which are the next accuracy-improvement milestones. All New/Improved rows reflect implemented contributions as of the filled date.",
          { size: 16, italics: true }
        ),
      ],
    },
  ],
});

const out =
  "/Users/nikhilkumar/Downloads/SLA_Contribution_Questionnaire_FILLED.docx";
const buf = await Packer.toBuffer(doc);
fs.writeFileSync(out, buf);
console.log("Wrote", out);
