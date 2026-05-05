# HAR MLOps Thesis — Explanation Notes

**Date:** February 24, 2026  
**Purpose:** Personal notes to understand the terms and ideas used in `mentor_questions.md`.  
These are **not** for the thesis itself; they are to help me think and talk clearly.

---

## 1. Monitoring thresholds and experiments

### 1.1 What is "synthetic drift injection"?

- **Idea:** I take some clean data and **artificially change it** so it looks like the data has drifted.  
- Examples:
  - Multiply accelerometer values by 1.5 to simulate a calibration change.
  - Add a constant offset to one axis.
  - Change the class distribution (e.g. make “rest” much more common).
- **Why:** Then I run the pipeline and see:
  - Does the drift detector fire?
  - At which threshold values does it miss drift or scream too often?
- This is a **simple, controlled way** to test if my monitoring works.

### 1.2 What is a "full sensitivity analysis"?

- **Sensitivity analysis** = check how the system behaves when I **change one parameter step by step**.
- For thresholds, it means:
  - Try many threshold values (e.g. 0.4, 0.5, 0.6, 0.7, …).
  - For each value, measure: false alarms, missed drift, detection delay, etc.
  - Make plots like “false positives vs threshold”.
- A **full sensitivity analysis** is:
  - More systematic and time‑consuming.
  - Closer to something you would put in a **paper**.
  - Harder to finish inside a master’s timeline.
- In the question, you are asking:  
  “Is a **small, simple experiment** enough, or do you want this big, heavy analysis?”

### 1.3 What is a "canonical config"?

- **Canonical** here means: the **one official source of truth**.
- A **canonical config file**:
  - Stores all threshold values (confidence, drift, transition rate, etc.).
  - Is used **by both**:
    - the offline pipeline script, and
    - the API / online monitor.
  - Is documented in the thesis.
- Right now:
  - Pipeline thresholds and API thresholds are **different**.
  - This can:
    - Confuse examiners (“Which one is correct?”).
    - Make experiments hard to reproduce.
    - Create situations where a bug appears in production but not in offline runs.
- In the questions, you ask:
  - “Which version should be the official one?”  
  - “Can I unify them into one canonical config?”

---

## 2. Prognosis model and CORAL

### 2.1 What is the prognosis model (in this thesis)?

- The **HAR model** predicts short‑term activities (e.g. rest, hand‑tapping, nail‑biting) from sensor data.
- The **prognosis model** is a **second model** that:
  - Takes **aggregated outputs** from the HAR model (for example: percentage of time in each behavior).
  - Predicts a **clinical outcome** or **risk level**, e.g.:
    - “High anxiety risk this week.”
    - “Symptoms getting worse compared to last month.”
- In the original plan:
  - There should be a data flow: **HAR → prognosis model**.
  - Intermediate results may be stored in a file or small database.
- In reality:
  - You focused on HAR, monitoring, and adaptation.
  - The prognosis model is **not implemented**.
- Q6 and Q7 basically ask:
  - “Is it OK that I **shift the main focus** away from prognosis?”
  - “What is the **minimum** I need to do for prognosis now (design only, placeholder, or full model)?“

### 2.2 What is "CORAL" here?

- **CORAL** usually means **CORrelation ALignment**:
  - A domain adaptation method.
  - It **matches the covariance** of features between source and target domains.
  - Idea: make features from new users look more like training users, so the model generalizes better.
- BUT: your mentor said “coral” in conversation, and it could also mean:
  - A **clinical score** or tool used in their group.
  - Some local shorthand for a method or project.
- That is why you ask:
  - “When you say ‘coral’, do you mean CORAL (the method), a clinical scale, or something else?”
  - “If it is CORAL, where should it sit? On HAR features, on prognosis features, or both?”

---

## 3. Online monitoring, Web UI, and automation

### 3.1 What is the “online monitoring” scenario?

In practice, your system can have **several ways of working**:

- **Offline script**:
  - Run `python run_pipeline.py` on CSV files.
  - Good for batch testing all 26 sessions.
- **API only**:
  - Send a request with a CSV file to FastAPI.
  - No human‑friendly interface.
- **Web UI (possible future)**:
  - A simple web page where:
    - You upload accelerometer/gyroscope CSV.
    - The backend calls the same API / pipeline.
    - You see predictions and monitoring results.

For **online monitoring** in the thesis:

- You propose to **simulate online** by:
  - Sending the 26 sessions one by one through the API.
  - Letting the monitor run after each file.
  - Optionally doing this from a simple Web UI.
- This is enough to:
  - Show how a new device or new dataset would be processed.
  - Show how you *could* retrain if labels are available.

### 3.2 Manual vs automatic retraining

- **Manual retrain**:
  - Monitor raises a warning.
  - Human reads the logs.
  - Human runs: `python run_pipeline.py --retrain`.
  - Simple to implement and safe.
- **Automatic retrain**:
  - CI/CD (e.g. GitHub Actions) watches the trigger state.
  - When a CRITICAL event appears, it:
    - Starts retraining.
    - Registers a new model.
    - Potentially deploys it.
- In the question you ask:
  - “For a **master’s** thesis, is manual retrain + good design explanation enough?”
  - Or: “Do I need a **fully closed loop** (detect drift → retrain → deploy)?”

### 3.3 Prometheus/Grafana vs MLflow

- **MLflow**:
  - Focus on **experiments**: training runs, metrics, models.
  - Good for offline evaluation and tracking.
- **Prometheus + Grafana**:
  - Focus on **live systems**: metrics over time, dashboards, alerts.
  - Good for monitoring a running API in production.
- In your questions:
  - You already have metrics defined and a Grafana dashboard JSON.
  - But you do **not** have a live Prometheus server running.
  - You ask if it is enough to:
    - Show the **design and code**,  
    - Or if you must also show **live dashboards** for the thesis.

---

## 4. Evaluation integrity: GroupKFold, LOSO, and minimum performance

### 4.1 What is subject‑wise evaluation?

- **Problem with window‑level split**:
  - The same person’s data is split into both train and validation.
  - The model sees that person’s patterns during training.
  - Validation looks better than it would on unseen people.
- **Subject‑wise evaluation**:
  - Make sure each person appears **only in train OR only in validation**, never both.
  - This is more realistic for “new user” performance.

### 4.2 What is GroupKFold?

- **GroupKFold** (in scikit‑learn):
  - You pass:
    - `X` = samples (here: windows),
    - `y` = labels,
    - `groups` = subject IDs.
  - It creates folds such that:
    - All windows from the same subject stay in the **same fold**.
  - Used when you have grouped data (like per‑user).

### 4.3 What is LOSO (Leave‑One‑Subject‑Out)?

- **LOSO**:
  - Each fold leaves **one subject out** as the test set.
  - Train on all other subjects.
  - Test on the left‑out subject.
  - Repeat for each subject.
- This is even stricter than GroupKFold and often used for wearable studies.

### 4.4 What is “minimum acceptable performance” here?

- Your question is:  
  “If I do subject‑wise evaluation and my scores drop, how low is still OK?”
- You want your mentor to **say a number** (e.g. macro F1 ≥ 0.75) so that:
  - You know if your current model is “good enough”.
  - You avoid a surprise later like “this is too low to pass”.

---

## 5. Data quality, PSI, and Z‑score drift

### 5.1 What is PSI (Population Stability Index) and its recalibration?

- **PSI** is a number that compares:
  - The distribution of a variable in training (reference) vs in current data.
  - Often used in credit scoring; small PSI = stable, large PSI = drift.
- Textbooks often say:
  - PSI < 0.1 → small shift  
  - PSI 0.1–0.2 → moderate  
  - PSI > 0.2 → big shift
- In your pipeline:
  - You use **multi‑channel aggregated PSI** (several sensors together).
  - You found that **0.10** caused constant false alarms.
  - Empirical calibration on your data suggested a better threshold ≈ **0.75**.
- So “PSI threshold recalibration” means:
  - You discovered that **literature defaults did not work** for your case.
  - You adjusted them **based on real data**.
  - This can be written as a small **methodological contribution**.

### 5.2 What is Z‑score drift?

- **Z‑score**:
  - Measures how many standard deviations a value is from the mean.
  - \( z = \frac{x - \mu}{\sigma} \).
- For drift:
  - You compute a statistic on current data (e.g. mean magnitude).
  - Compare it to the training distribution (mean, std).
  - High absolute z‑score (e.g. |z| > 2) means “unusual compared to training”.
- In your monitor:
  - You aggregate across **6 sensor channels**.
  - This tends to make the overall z‑score larger.
  - You are asking whether the **standard 2σ rule** is still OK, or if you must **recalibrate** like PSI.

---

## 6. Adaptation methods: AdaBN, TENT, and self‑consistency filter

### 6.1 What is AdaBN (Adaptive Batch Normalization)?

- **Goal:** Adapt the model to a new user **without labels**.
- Batch Normalization (BN) layers store:
  - Running mean and variance of activations from training data.
- **AdaBN idea**:
  - When you see new user data, you **update BN statistics** using that data.
  - You do **not** change weights, only the BN stats.
- Effect:
  - Adjusts the internal feature distribution to match the new domain.
  - Often improves performance on new users with minimal risk.

### 6.2 What is TENT (Test‑Time Entropy Minimization)?

- **Goal:** Also adapt without labels, but by **updating weights**.
- Idea:
  - For each test batch, compute prediction entropy (uncertainty).
  - Take a gradient step on the model weights to **reduce entropy**.
  - Encourage the model to make **confident** predictions on new data.
- Risks:
  - If implemented incorrectly, it can **destroy BN stats** or overfit.
  - In your case, TENT was overwriting AdaBN’s BN statistics.

### 6.3 What is the self‑consistency filter and why do rare classes matter?

- In pseudo‑labeling, you:
  - Take the model’s predictions on unlabeled data.
  - Use only **high‑confidence** predictions as “pseudo labels” for retraining.
- In your pipeline:
  - You also apply a **self‑consistency filter** to source data:
    - Keep only windows where the pre‑trained model agrees with the true label.
    - This left you with only about **14.5%** of labeled source windows.
- Problem for rare classes:
  - For classes like nail‑biting, knuckle‑cracking, etc., the model may:
    - Never be very confident.
    - Fail the self‑consistency filter often.
  - Then these classes **almost disappear** from retraining.
  - Over time, the model may **forget rare classes** (“class collapse”).
- Your question is:
  - “Should I run an experiment **with vs without** this filter to see if it is really helping, or just describe the risk in words?”

Note: you observed that many of the 26 new sessions have mostly **hand‑tapping** motion. This makes the class imbalance problem and the risk of class collapse even more important in your explanation.

---

## 7. DANN and MMD

### 7.1 What is DANN (Domain‑Adversarial Neural Network)?

- **Goal:** Learn features that:
  - Are good for the main task (e.g. activity classification).
  - Are **domain‑invariant** (model cannot tell which user/domain data came from).
- How:
  - Add a **domain classifier** head that tries to predict the domain (source vs target).
  - Add a **gradient reversal layer** so that the feature extractor learns to **confuse** this domain classifier.
- In your code:
  - DANN is **referenced** but not implemented (raises `NotImplementedError`).
  - You ask whether to:
    - Implement it,  
    - Remove it, or  
    - Keep it as clearly labeled future work.

### 7.2 What is MMD (Maximum Mean Discrepancy)?

- **Goal:** Measure or reduce the distance between **two distributions**.
- MMD compares:
  - The mean of features in source data vs target data in a high‑dimensional feature space.
- In domain adaptation:
  - You can add an MMD **regularization term** so features from source and target become more similar.
- In your code:
  - MMD is mentioned but not implemented.
  - Same decision as for DANN: implement now or keep as future work.

---

## 8. Freezing the code and “what must be finished vs future work”

### 8.1 What does “freezing the code” mean?

- **Freeze the code** = choose one **final commit** that represents the thesis version.
- After freezing:
  - No more feature changes (only small bug fixes if really needed).
  - You use **commit‑pinned links** in the thesis:
    - Example: `https://github.com/.../blob/<COMMIT_SHA>/src/train.py#L123`
  - This means:
    - Examiners can always see exactly the code you refer to.
    - Links do not break when you keep developing later.

### 8.2 What does “what must be finished vs future work” mean?

- This is about **scope management**:
  - Which parts **must** be fully implemented and evaluated **before submission**?
  - Which parts you can:
    - Implement partially, or
    - Only design and describe as **future work** (Chapter 6).
- Examples:
  - **Must finish** (probably):
    - Subject‑wise evaluation.
    - Main monitoring thresholds and their justification.
    - Main adaptation experiments (AdaBN/TENT baseline ablations).
  - **Future work** candidates:
    - Extra drift methods (Wasserstein, OOD, sensor placement).
    - Full automatic CI/CD loop.
    - DANN and MMD.
- In Q34 you are asking your mentor to **explicitly mark** which advanced features:
  - Need results now, and
  - Can safely be left as “implemented but evaluation is future work”.

---

## 9. Exams in March/April — what should be ready?

Given you have exams in March and April:

- **Before / during March** (while exams are happening), realistic goals:
  - Finish subject‑wise evaluation code (GroupKFold or LOSO).
  - Run at least **one clean set of main experiments**:
    - Baseline HAR,
    - AdaBN,
    - TENT (with fix),
    - Maybe pseudo‑labeling with/without filter.
  - Decide (with your mentor) the **final scope** using this mentor‑questions email.
- **After exams, early April**:
  - Clean up results, tables, and plots.
  - Write core thesis chapters:
    - Methods,
    - Results,
    - Discussion & future work.
  - Freeze code at a stable commit and wire thesis references to that commit.

These notes are just for you; the mentor email will tell you more clearly what *they* see as “must‑have” before April.

