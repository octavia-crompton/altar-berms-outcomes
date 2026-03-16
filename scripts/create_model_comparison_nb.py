#!/usr/bin/env python3
"""Create models - model comparison.ipynb with all cells."""
import json, os

NB_PATH = os.path.join(os.path.dirname(__file__), "..",
                       "notebooks", "models - model comparison.ipynb")

cells = []

# ═══════════════════════════════════════════════════════════════════
# Cell 1: markdown header
# ═══════════════════════════════════════════════════════════════════
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# Model Comparison \u2014 RF vs Logistic Regression\n",
        "\n",
        "Compares Random Forest and L2-penalised Logistic Regression for predicting\n",
        "berm **condition** (Intact) and **vegetation response** (Effective).\n",
        "\n",
        "**Workflow:**\n",
        "1. Define predictor scenarios (geomorphology, soil, length, all combined)\n",
        "2. Baseline: fit RF + Logistic across all scenarios (CV AUC comparison)\n",
        "3. Feature selection via RFECV (logistic backbone) on the \"all predictors\" set\n",
        "4. Refit both models on RFECV-selected features and compare\n",
        "5. Feature importance: RF permutation importance + Logistic |coefficients|\n",
        "\n",
        "Loads `../data/merged.csv` produced by `data processing - condition vegetation.ipynb`."
    ]
})

# ═══════════════════════════════════════════════════════════════════
# Cell 2: imports
# ═══════════════════════════════════════════════════════════════════
cells.append({
    "cell_type": "code",
    "metadata": {},
    "outputs": [],
    "execution_count": None,
    "source": [
        "# \u2500\u2500 1. Imports \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n",
        "import sys as _sys\n",
        "_sys.path.insert(0, '../src')\n",
        "from constants import (\n",
        "    INTACT_COL, DEGRADED_COL,\n",
        "    MODEL_CLR_CONDITION, MODEL_CLR_VEGRESPONSE, MODEL_CLR_CHANCE,\n",
        ")\n",
        "from analysis import (\n",
        "    fit_rf_binary, _unique_preserve, _coerce_binary,\n",
        "    PRETTY_LABELS, _clean_predictor_name,\n",
        ")\n",
        "from registry import register_outcomes_figure\n",
        "\n",
        "import os\n",
        "import numpy as np\n",
        "import pandas as pd\n",
        "import matplotlib.pyplot as plt\n",
        "import warnings\n",
        "warnings.filterwarnings('ignore', category=FutureWarning)\n",
        "\n",
        "from sklearn.model_selection import StratifiedKFold, train_test_split, cross_validate\n",
        "from sklearn.preprocessing import OneHotEncoder, StandardScaler\n",
        "from sklearn.compose import ColumnTransformer\n",
        "from sklearn.pipeline import Pipeline\n",
        "from sklearn.impute import SimpleImputer\n",
        "from sklearn.linear_model import LogisticRegression\n",
        "from sklearn.ensemble import RandomForestClassifier\n",
        "from sklearn.feature_selection import RFECV\n",
        "from sklearn.metrics import roc_auc_score\n",
        "from sklearn.inspection import permutation_importance\n",
        "from IPython.display import display\n",
        "\n",
        "pd.set_option('display.max_columns', 50)\n",
        "print('Imports OK')"
    ]
})

# ═══════════════════════════════════════════════════════════════════
# Cell 3: load data
# ═══════════════════════════════════════════════════════════════════
cells.append({
    "cell_type": "code",
    "metadata": {},
    "outputs": [],
    "execution_count": None,
    "source": [
        "# \u2500\u2500 2. Load data \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n",
        "data = pd.read_csv('../data/merged.csv')\n",
        "df = data.loc[data['Structure_'].isna()].copy() if 'Structure_' in data.columns else data.copy()\n",
        "print(f'Loaded {len(data):,} rows \u2192 df: {len(df):,} rows (after dropping artificial structures)')"
    ]
})

# ═══════════════════════════════════════════════════════════════════
# Cell 4: predictor scenarios
# ═══════════════════════════════════════════════════════════════════
cells.append({
    "cell_type": "code",
    "metadata": {},
    "outputs": [],
    "execution_count": None,
    "source": [
        "# \u2500\u2500 3. Predictor scenario definitions \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n",
        "treat_as = {\n",
        "    'Shape_Leng': 'numeric',\n",
        "    'High_Clay':  'categorical',\n",
        "}\n",
        "\n",
        "_geo_preds  = ['Landform', 'slope_200', 'FA_30_max']\n",
        "_soil_preds = ['Texture', 'Soil_Development', 'TypicalProfile']\n",
        "_len_preds  = ['Shape_Leng', 'Berm_Length_Class']\n",
        "_all_preds  = _unique_preserve(_geo_preds + _soil_preds + _len_preds)\n",
        "\n",
        "scenario_predictors = {\n",
        "    'landscape_geomorphology_only': _geo_preds,\n",
        "    'soil_only':                    _soil_preds,\n",
        "    'shape_length_only':            _len_preds,\n",
        "    'all_predictors':               _all_preds,\n",
        "}\n",
        "\n",
        "_targets = ['Intact', 'Effective']\n",
        "print(f'All predictors: {_all_preds}')\n",
        "print(f'Targets: {_targets}')"
    ]
})

# ═══════════════════════════════════════════════════════════════════
# Cell 5: unified pipeline builder
# ═══════════════════════════════════════════════════════════════════
cells.append({
    "cell_type": "code",
    "metadata": {},
    "outputs": [],
    "execution_count": None,
    "source": [
        "# \u2500\u2500 4. Unified model pipeline builder \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n",
        "\n",
        "def _build_pipeline(model_type, predictors, treat_as_map=None):\n",
        "    \"\"\"Build a sklearn Pipeline for RF or Logistic.\"\"\"\n",
        "    treat_as_map = treat_as_map or {}\n",
        "    cat_cols, num_cols = [], []\n",
        "    for c in predictors:\n",
        "        ta = treat_as_map.get(c)\n",
        "        if ta == 'categorical':\n",
        "            cat_cols.append(c)\n",
        "        elif ta == 'numeric':\n",
        "            num_cols.append(c)\n",
        "        elif df[c].dtype == object or str(df[c].dtype).startswith('category'):\n",
        "            cat_cols.append(c)\n",
        "        else:\n",
        "            num_cols.append(c)\n",
        "\n",
        "    pre = ColumnTransformer(\n",
        "        transformers=[\n",
        "            ('num', Pipeline([\n",
        "                ('impute', SimpleImputer(strategy='median')),\n",
        "                ('scale', StandardScaler()),\n",
        "            ]), num_cols),\n",
        "            ('cat', Pipeline([\n",
        "                ('impute', SimpleImputer(strategy='most_frequent')),\n",
        "                ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),\n",
        "            ]), cat_cols),\n",
        "        ],\n",
        "        remainder='drop',\n",
        "    )\n",
        "\n",
        "    if model_type == 'RF':\n",
        "        clf = RandomForestClassifier(\n",
        "            n_estimators=300, min_samples_leaf=2,\n",
        "            class_weight='balanced', random_state=0, n_jobs=-1,\n",
        "        )\n",
        "    elif model_type == 'Logistic':\n",
        "        clf = LogisticRegression(\n",
        "            C=1.0, penalty='l2', max_iter=2000,\n",
        "            class_weight='balanced', solver='lbfgs', random_state=0,\n",
        "        )\n",
        "    else:\n",
        "        raise ValueError(f'Unknown model_type: {model_type}')\n",
        "\n",
        "    return Pipeline([('pre', pre), ('clf', clf)])\n",
        "\n",
        "\n",
        "def _fit_and_evaluate(model_type, predictors, target, treat_as_map=None,\n",
        "                      test_size=0.25, random_state=0):\n",
        "    \"\"\"\n",
        "    Fit pipeline, return (pipeline, metrics_dict, pi_series).\n",
        "    metrics_dict: 'cv' → dict of (mean, sd) tuples; 'holdout' → dict.\n",
        "    pi_series: permutation importance on holdout set.\n",
        "    \"\"\"\n",
        "    treat_as_map = treat_as_map or {}\n",
        "    sub = df[predictors + [target]].copy()\n",
        "    sub[target] = _coerce_binary(sub[target])\n",
        "    sub = sub.dropna(subset=[target])\n",
        "\n",
        "    X = sub[predictors]\n",
        "    yv = sub[target].astype(int)\n",
        "\n",
        "    pipe = _build_pipeline(model_type, predictors, treat_as_map)\n",
        "\n",
        "    X_tr, X_te, y_tr, y_te = train_test_split(\n",
        "        X, yv, test_size=test_size, stratify=yv, random_state=random_state)\n",
        "    pipe.fit(X_tr, y_tr)\n",
        "\n",
        "    holdout_auc = roc_auc_score(y_te, pipe.predict_proba(X_te)[:, 1])\n",
        "\n",
        "    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)\n",
        "    cv_scores = cross_validate(\n",
        "        pipe, X, yv, cv=cv,\n",
        "        scoring={'auc': 'roc_auc', 'bal_acc': 'balanced_accuracy', 'f1': 'f1'},\n",
        "        n_jobs=-1, return_train_score=False,\n",
        "    )\n",
        "    cv_summary = {\n",
        "        k.replace('test_', ''): (float(np.mean(v)), float(np.std(v)))\n",
        "        for k, v in cv_scores.items() if k.startswith('test_')\n",
        "    }\n",
        "\n",
        "    pi = permutation_importance(\n",
        "        pipe, X_te, y_te, scoring='roc_auc',\n",
        "        n_repeats=30, random_state=random_state, n_jobs=-1,\n",
        "    )\n",
        "    pi_series = pd.Series(pi.importances_mean, index=predictors).sort_values(ascending=False)\n",
        "\n",
        "    metrics = {\n",
        "        'cv': cv_summary,\n",
        "        'holdout': {'auc': float(holdout_auc)},\n",
        "        'n': int(len(X)),\n",
        "    }\n",
        "    return pipe, metrics, pi_series\n",
        "\n",
        "\n",
        "print('Pipeline builder & evaluator defined')"
    ]
})

# ═══════════════════════════════════════════════════════════════════
# Cell 6: markdown section
# ═══════════════════════════════════════════════════════════════════
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": ["## Baseline: all scenarios \u00d7 both models"]
})

# ═══════════════════════════════════════════════════════════════════
# Cell 7: baseline scenario sweep
# ═══════════════════════════════════════════════════════════════════
cells.append({
    "cell_type": "code",
    "metadata": {},
    "outputs": [],
    "execution_count": None,
    "source": [
        "# \u2500\u2500 5. Baseline scenario sweep \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n",
        "_model_types = ['RF', 'Logistic']\n",
        "baseline_rows = []\n",
        "baseline_results = {}   # (scenario, model_type, target) \u2192 (pipe, metrics, pi)\n",
        "\n",
        "for _scenario, _preds in scenario_predictors.items():\n",
        "    _preds_run = [p for p in _preds if p in df.columns]\n",
        "    if not _preds_run:\n",
        "        print(f'Skipping {_scenario}: no columns found')\n",
        "        continue\n",
        "    for _mt in _model_types:\n",
        "        for _tgt in _targets:\n",
        "            try:\n",
        "                _pipe, _met, _pi = _fit_and_evaluate(\n",
        "                    _mt, _preds_run, _tgt, treat_as_map=treat_as)\n",
        "            except Exception as _e:\n",
        "                print(f'  SKIP {_scenario}/{_mt}/{_tgt}: {_e}')\n",
        "                continue\n",
        "\n",
        "            baseline_results[(_scenario, _mt, _tgt)] = (_pipe, _met, _pi)\n",
        "            baseline_rows.append({\n",
        "                'scenario':    _scenario,\n",
        "                'model':       _mt,\n",
        "                'target':      _tgt,\n",
        "                'cv_auc_mean': _met['cv']['auc'][0],\n",
        "                'cv_auc_sd':   _met['cv']['auc'][1],\n",
        "                'holdout_auc': _met['holdout']['auc'],\n",
        "                'n':           _met['n'],\n",
        "            })\n",
        "\n",
        "baseline_df = pd.DataFrame(baseline_rows)\n",
        "print(f'\\nDone \u2014 {len(baseline_rows)} fits')\n",
        "display(baseline_df.sort_values(['target', 'scenario', 'model']))"
    ]
})

# ═══════════════════════════════════════════════════════════════════
# Cell 8: baseline dot-plot
# ═══════════════════════════════════════════════════════════════════
cells.append({
    "cell_type": "code",
    "metadata": {},
    "outputs": [],
    "execution_count": None,
    "source": [
        "# \u2500\u2500 6. Dot-plot: scenario \u00d7 model \u00d7 target \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n",
        "_key_order = ['landscape_geomorphology_only', 'soil_only',\n",
        "              'shape_length_only', 'all_predictors']\n",
        "_label_map = {\n",
        "    'landscape_geomorphology_only': 'Geomorphology only',\n",
        "    'soil_only':                    'Soil only',\n",
        "    'shape_length_only':            'Shape length only',\n",
        "    'all_predictors':               'All predictors',\n",
        "}\n",
        "\n",
        "fig1, axes = plt.subplots(1, 2, figsize=(15, 5), sharey=True)\n",
        "_y_pos = np.arange(len(_key_order))\n",
        "_jitter = 0.12\n",
        "\n",
        "_clr = {'Intact': MODEL_CLR_CONDITION, 'Effective': MODEL_CLR_VEGRESPONSE}\n",
        "_marker = {'RF': 'o', 'Logistic': 's'}\n",
        "_ms = {'RF': 10, 'Logistic': 9}\n",
        "\n",
        "for ax_idx, _tgt in enumerate(_targets):\n",
        "    ax = axes[ax_idx]\n",
        "    _sub = baseline_df[baseline_df['target'] == _tgt].copy()\n",
        "    _sub['order'] = _sub['scenario'].map({s: i for i, s in enumerate(_key_order)})\n",
        "    _sub = _sub.sort_values('order')\n",
        "\n",
        "    for _mt_idx, _mt in enumerate(_model_types):\n",
        "        _rows = _sub[_sub['model'] == _mt]\n",
        "        _y = _rows['order'].values + (_mt_idx - 0.5) * _jitter * 2\n",
        "        ax.errorbar(\n",
        "            _rows['cv_auc_mean'].values, _y,\n",
        "            xerr=_rows['cv_auc_sd'].values,\n",
        "            fmt=_marker[_mt], color=_clr[_tgt],\n",
        "            markersize=_ms[_mt], elinewidth=1.3, capsize=3.5,\n",
        "            alpha=0.6 if _mt == 'Logistic' else 0.9,\n",
        "            label=_mt, zorder=3,\n",
        "        )\n",
        "        # connect RF\u2013Logistic for same scenario\n",
        "        for _, _row in _rows.iterrows():\n",
        "            _rf_row = _sub[(_sub['model'] == 'RF') & (_sub['scenario'] == _row['scenario'])]\n",
        "            if not _rf_row.empty and _mt == 'Logistic':\n",
        "                ax.plot(\n",
        "                    [_rf_row['cv_auc_mean'].values[0], _row['cv_auc_mean']],\n",
        "                    [_rf_row['order'].values[0] - _jitter,\n",
        "                     _row['order'] + _jitter],\n",
        "                    color='#d0d0d0', linewidth=1.5, zorder=1)\n",
        "\n",
        "    ax.axvline(0.5, color=MODEL_CLR_CHANCE, ls='--', lw=1.2, label='Chance', zorder=0)\n",
        "    ax.set_yticks(_y_pos)\n",
        "    ax.set_yticklabels([_label_map[s] for s in _key_order], fontsize=11)\n",
        "    ax.invert_yaxis()\n",
        "    ax.set_xlim(0.35, 1.02)\n",
        "    ax.set_xlabel('Cross-validated AUC (mean \u00b1 SD)', fontsize=11)\n",
        "    _title = 'condition' if _tgt == 'Intact' else 'vegetation response'\n",
        "    ax.set_title(f'Predicting {_title}',\n",
        "                 fontsize=12, fontweight='normal', loc='left')\n",
        "    ax.legend(fontsize=10, loc='lower right', framealpha=0.9)\n",
        "    ax.spines[['top', 'right']].set_visible(False)\n",
        "\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "print('Baseline comparison plotted')"
    ]
})

# ═══════════════════════════════════════════════════════════════════
# Cell 9: RFECV markdown
# ═══════════════════════════════════════════════════════════════════
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## Feature selection \u2014 RFECV (logistic backbone)\n",
        "\n",
        "Recursive feature elimination with cross-validation using L2 logistic regression.\n",
        "Operates on the one-hot-encoded feature space; a predictor is **kept** if\n",
        "at least one of its dummy columns is selected."
    ]
})

# ═══════════════════════════════════════════════════════════════════
# Cell 10: RFECV code
# ═══════════════════════════════════════════════════════════════════
cells.append({
    "cell_type": "code",
    "metadata": {},
    "outputs": [],
    "execution_count": None,
    "source": [
        "# \u2500\u2500 7. RFECV feature selection on all_predictors \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n",
        "\n",
        "def _rfecv_select(predictors, target, treat_as_map=None, random_state=0):\n",
        "    \"\"\"\n",
        "    Run RFECV on the encoded feature matrix and map surviving dummy columns\n",
        "    back to original predictor names.\n",
        "    \"\"\"\n",
        "    treat_as_map = treat_as_map or {}\n",
        "    sub = df[predictors + [target]].copy()\n",
        "    sub[target] = _coerce_binary(sub[target])\n",
        "    sub = sub.dropna(subset=[target])\n",
        "    X = sub[predictors]\n",
        "    yv = sub[target].astype(int).values\n",
        "\n",
        "    # Split categorical / numeric\n",
        "    cat_cols, num_cols = [], []\n",
        "    for c in predictors:\n",
        "        ta = treat_as_map.get(c)\n",
        "        if ta == 'categorical':\n",
        "            cat_cols.append(c)\n",
        "        elif ta == 'numeric':\n",
        "            num_cols.append(c)\n",
        "        elif X[c].dtype == object or str(X[c].dtype).startswith('category'):\n",
        "            cat_cols.append(c)\n",
        "        else:\n",
        "            num_cols.append(c)\n",
        "\n",
        "    pre = ColumnTransformer(\n",
        "        transformers=[\n",
        "            ('num', Pipeline([\n",
        "                ('impute', SimpleImputer(strategy='median')),\n",
        "                ('scale', StandardScaler()),\n",
        "            ]), num_cols),\n",
        "            ('cat', Pipeline([\n",
        "                ('impute', SimpleImputer(strategy='most_frequent')),\n",
        "                ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),\n",
        "            ]), cat_cols),\n",
        "        ],\n",
        "        remainder='drop',\n",
        "    )\n",
        "\n",
        "    X_enc = pre.fit_transform(X)\n",
        "\n",
        "    # Build encoded column \u2192 original predictor mapping\n",
        "    _enc_names = []\n",
        "    _col_to_pred = {}\n",
        "    idx = 0\n",
        "    for c in num_cols:\n",
        "        _enc_names.append(c)\n",
        "        _col_to_pred[idx] = c\n",
        "        idx += 1\n",
        "    ohe = pre.named_transformers_['cat'].named_steps['onehot']\n",
        "    for name in ohe.get_feature_names_out(cat_cols):\n",
        "        # name looks like 'Landform_Fan terraces'\n",
        "        _orig = name.split('_', 1)[0]\n",
        "        _enc_names.append(name)\n",
        "        _col_to_pred[idx] = _orig\n",
        "        idx += 1\n",
        "\n",
        "    # RFECV with logistic backbone\n",
        "    _lr = LogisticRegression(\n",
        "        C=1.0, penalty='l2', max_iter=2000,\n",
        "        class_weight='balanced', solver='lbfgs', random_state=random_state,\n",
        "    )\n",
        "    _cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)\n",
        "    _rfecv = RFECV(\n",
        "        estimator=_lr, step=1, cv=_cv, scoring='roc_auc',\n",
        "        min_features_to_select=1, n_jobs=-1,\n",
        "    )\n",
        "    _rfecv.fit(X_enc, yv)\n",
        "\n",
        "    # Map selected encoded columns back to original predictors\n",
        "    _selected_encoded = np.where(_rfecv.support_)[0]\n",
        "    _selected_orig = sorted(set(_col_to_pred[i] for i in _selected_encoded),\n",
        "                            key=lambda x: predictors.index(x))\n",
        "\n",
        "    return {\n",
        "        'selected_predictors': _selected_orig,\n",
        "        'rfecv': _rfecv,\n",
        "        'encoded_feature_names': _enc_names,\n",
        "        'support_mask': _rfecv.support_,\n",
        "        'col_to_predictor': _col_to_pred,\n",
        "        'n_encoded_total': len(_enc_names),\n",
        "        'n_encoded_selected': int(_rfecv.support_.sum()),\n",
        "    }\n",
        "\n",
        "\n",
        "# Run for both targets\n",
        "rfecv_results = {}\n",
        "for _tgt in _targets:\n",
        "    print(f'\\n{\"=\"*60}')\n",
        "    print(f'  RFECV for {_tgt}')\n",
        "    print(f'{\"=\"*60}')\n",
        "    _res = _rfecv_select(_all_preds, _tgt, treat_as_map=treat_as)\n",
        "    rfecv_results[_tgt] = _res\n",
        "    print(f'  Encoded features: {_res[\"n_encoded_total\"]} \u2192 selected: {_res[\"n_encoded_selected\"]}')\n",
        "    print(f'  Original predictors selected ({len(_res[\"selected_predictors\"])} / {len(_all_preds)}):')\n",
        "    print(f'    {_res[\"selected_predictors\"]}')\n",
        "    _dropped = [p for p in _all_preds if p not in _res['selected_predictors']]\n",
        "    if _dropped:\n",
        "        print(f'  Dropped: {_dropped}')\n",
        "    print(f'  Optimal CV AUC: {_res[\"rfecv\"].cv_results_[\"mean_test_score\"].max():.3f}')"
    ]
})

# ═══════════════════════════════════════════════════════════════════
# Cell 11: feature selection summary table
# ═══════════════════════════════════════════════════════════════════
cells.append({
    "cell_type": "code",
    "metadata": {},
    "outputs": [],
    "execution_count": None,
    "source": [
        "# \u2500\u2500 8. Feature selection summary table \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n",
        "_sel_rows = []\n",
        "for _p in _all_preds:\n",
        "    _row = {'Predictor': _clean_predictor_name(_p)}\n",
        "    for _tgt in _targets:\n",
        "        _row[f'Selected ({_tgt})'] = _p in rfecv_results[_tgt]['selected_predictors']\n",
        "    _sel_rows.append(_row)\n",
        "\n",
        "_sel_table = pd.DataFrame(_sel_rows)\n",
        "# Style True/False as checkmarks\n",
        "for _c in [c for c in _sel_table.columns if c.startswith('Selected')]:\n",
        "    _sel_table[_c] = _sel_table[_c].map({True: '\u2713', False: '\u2717'})\n",
        "\n",
        "display(_sel_table)\n",
        "\n",
        "# Save\n",
        "os.makedirs('../data/summary', exist_ok=True)\n",
        "_sel_table.to_csv('../data/summary/rfecv_feature_selection.csv', index=False)\n",
        "print('Saved: ../data/summary/rfecv_feature_selection.csv')"
    ]
})

# ═══════════════════════════════════════════════════════════════════
# Cell 12: refit markdown
# ═══════════════════════════════════════════════════════════════════
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": ["## Refit on RFECV-selected features"]
})

# ═══════════════════════════════════════════════════════════════════
# Cell 13: refit on selected features
# ═══════════════════════════════════════════════════════════════════
cells.append({
    "cell_type": "code",
    "metadata": {},
    "outputs": [],
    "execution_count": None,
    "source": [
        "# \u2500\u2500 9. Refit RF + Logistic on selected features \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n",
        "_refit_rows = []\n",
        "refit_results = {}  # (model_type, target) \u2192 (pipe, metrics, pi)\n",
        "\n",
        "for _tgt in _targets:\n",
        "    _sel_preds = rfecv_results[_tgt]['selected_predictors']\n",
        "    for _mt in _model_types:\n",
        "        print(f'\\nRefitting {_mt} for {_tgt} with {len(_sel_preds)} selected predictors...')\n",
        "        _pipe, _met, _pi = _fit_and_evaluate(\n",
        "            _mt, _sel_preds, _tgt, treat_as_map=treat_as)\n",
        "        refit_results[(_mt, _tgt)] = (_pipe, _met, _pi)\n",
        "\n",
        "        # Before (all_predictors) metrics\n",
        "        _before_key = ('all_predictors', _mt, _tgt)\n",
        "        if _before_key in baseline_results:\n",
        "            _before_auc = baseline_results[_before_key][1]['cv']['auc'][0]\n",
        "            _before_sd  = baseline_results[_before_key][1]['cv']['auc'][1]\n",
        "        else:\n",
        "            _before_auc, _before_sd = np.nan, np.nan\n",
        "\n",
        "        _after_auc = _met['cv']['auc'][0]\n",
        "        _after_sd  = _met['cv']['auc'][1]\n",
        "\n",
        "        _refit_rows.append({\n",
        "            'model':       _mt,\n",
        "            'target':      _tgt,\n",
        "            'n_pred_all':  len(_all_preds),\n",
        "            'n_pred_sel':  len(_sel_preds),\n",
        "            'auc_before':  _before_auc,\n",
        "            'sd_before':   _before_sd,\n",
        "            'auc_after':   _after_auc,\n",
        "            'sd_after':    _after_sd,\n",
        "            'delta_auc':   _after_auc - _before_auc,\n",
        "        })\n",
        "        print(f'  AUC: {_before_auc:.3f} \u2192 {_after_auc:.3f}  (\u0394 {_after_auc - _before_auc:+.3f})')\n",
        "\n",
        "_refit_df = pd.DataFrame(_refit_rows)\n",
        "display(_refit_df)"
    ]
})

# ═══════════════════════════════════════════════════════════════════
# Cell 14: before vs after bar chart
# ═══════════════════════════════════════════════════════════════════
cells.append({
    "cell_type": "code",
    "metadata": {},
    "outputs": [],
    "execution_count": None,
    "source": [
        "# \u2500\u2500 10. Before vs After feature selection bar chart \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n",
        "fig2, axes2 = plt.subplots(1, 2, figsize=(13, 5), sharey=True)\n",
        "\n",
        "for ax_idx, _tgt in enumerate(_targets):\n",
        "    ax = axes2[ax_idx]\n",
        "    _sub = _refit_df[_refit_df['target'] == _tgt]\n",
        "    _x = np.arange(len(_model_types))\n",
        "    _w = 0.32\n",
        "\n",
        "    _clr_before = '#bbbbbb'\n",
        "    _clr_after  = MODEL_CLR_CONDITION if _tgt == 'Intact' else MODEL_CLR_VEGRESPONSE\n",
        "\n",
        "    for i, _mt in enumerate(_model_types):\n",
        "        _r = _sub[_sub['model'] == _mt].iloc[0]\n",
        "        ax.bar(i - _w/2, _r['auc_before'], _w, yerr=_r['sd_before'],\n",
        "               color=_clr_before, edgecolor='black', lw=0.8, capsize=4,\n",
        "               label='All predictors' if i == 0 else '')\n",
        "        ax.bar(i + _w/2, _r['auc_after'], _w, yerr=_r['sd_after'],\n",
        "               color=_clr_after, edgecolor='black', lw=0.8, capsize=4,\n",
        "               label='RFECV-selected' if i == 0 else '')\n",
        "        # value labels\n",
        "        ax.text(i - _w/2, _r['auc_before'] + _r['sd_before'] + 0.01,\n",
        "                f'{_r[\"auc_before\"]:.3f}', ha='center', va='bottom', fontsize=9)\n",
        "        ax.text(i + _w/2, _r['auc_after'] + _r['sd_after'] + 0.01,\n",
        "                f'{_r[\"auc_after\"]:.3f}', ha='center', va='bottom', fontsize=9)\n",
        "\n",
        "    ax.axhline(0.5, color=MODEL_CLR_CHANCE, ls='--', lw=1, label='Chance')\n",
        "    ax.set_xticks(_x)\n",
        "    ax.set_xticklabels(_model_types, fontsize=11)\n",
        "    ax.set_ylabel('CV AUC', fontsize=11)\n",
        "    ax.set_ylim(0.35, 0.95)\n",
        "    _title = 'condition' if _tgt == 'Intact' else 'vegetation response'\n",
        "    ax.set_title(f'Predicting {_title}',\n",
        "                 fontsize=12, fontweight='normal', loc='left')\n",
        "    ax.legend(fontsize=10, loc='lower right', framealpha=0.9)\n",
        "    ax.spines[['top', 'right']].set_visible(False)\n",
        "    ax.grid(axis='y', alpha=0.2)\n",
        "\n",
        "fig2.suptitle('Effect of RFECV feature selection on model performance',\n",
        "              fontsize=13, fontweight='normal', y=1.01)\n",
        "plt.tight_layout()\n",
        "plt.show()"
    ]
})

# ═══════════════════════════════════════════════════════════════════
# Cell 15: importance markdown
# ═══════════════════════════════════════════════════════════════════
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": ["## Feature importance \u2014 RF permutation vs Logistic coefficients"]
})

# ═══════════════════════════════════════════════════════════════════
# Cell 16: feature importance comparison
# ═══════════════════════════════════════════════════════════════════
cells.append({
    "cell_type": "code",
    "metadata": {},
    "outputs": [],
    "execution_count": None,
    "source": [
        "# \u2500\u2500 11. Feature importance comparison \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n",
        "\n",
        "def _logistic_coef_importance(pipe, predictors, treat_as_map=None):\n",
        "    \"\"\"\n",
        "    Extract absolute logistic coefficients from a fitted pipeline and\n",
        "    aggregate back to original predictor level (max |coef| per predictor).\n",
        "    \"\"\"\n",
        "    treat_as_map = treat_as_map or {}\n",
        "    coefs = pipe.named_steps['clf'].coef_.ravel()\n",
        "    pre = pipe.named_steps['pre']\n",
        "\n",
        "    cat_cols, num_cols = [], []\n",
        "    for c in predictors:\n",
        "        ta = treat_as_map.get(c)\n",
        "        if ta == 'categorical':\n",
        "            cat_cols.append(c)\n",
        "        elif ta == 'numeric':\n",
        "            num_cols.append(c)\n",
        "        elif df[c].dtype == object or str(df[c].dtype).startswith('category'):\n",
        "            cat_cols.append(c)\n",
        "        else:\n",
        "            num_cols.append(c)\n",
        "\n",
        "    _agg = {}\n",
        "    idx = 0\n",
        "    for c in num_cols:\n",
        "        _agg[c] = abs(coefs[idx])\n",
        "        idx += 1\n",
        "    ohe = pre.named_transformers_['cat'].named_steps['onehot']\n",
        "    for name in ohe.get_feature_names_out(cat_cols):\n",
        "        _orig = name.split('_', 1)[0]\n",
        "        _agg[_orig] = max(_agg.get(_orig, 0), abs(coefs[idx]))\n",
        "        idx += 1\n",
        "\n",
        "    return pd.Series(_agg).sort_values(ascending=False)\n",
        "\n",
        "\n",
        "fig3, axes3 = plt.subplots(2, 2, figsize=(15, 10))\n",
        "\n",
        "_N_FEAT = 8\n",
        "\n",
        "for col_idx, _tgt in enumerate(_targets):\n",
        "    _sel_preds = rfecv_results[_tgt]['selected_predictors']\n",
        "    _clr = MODEL_CLR_CONDITION if _tgt == 'Intact' else MODEL_CLR_VEGRESPONSE\n",
        "    _tgt_label = 'condition' if _tgt == 'Intact' else 'vegetation response'\n",
        "\n",
        "    # Row 0: RF permutation importance\n",
        "    _ax_rf = axes3[0, col_idx]\n",
        "    _pi_rf = refit_results[('RF', _tgt)][2].head(_N_FEAT)\n",
        "    _pi_rf_pretty = _pi_rf.rename(index=lambda x: _clean_predictor_name(x))\n",
        "    _y = np.arange(len(_pi_rf_pretty))\n",
        "    _ax_rf.barh(_y, _pi_rf_pretty.values, color=_clr, alpha=0.85,\n",
        "                edgecolor='white', lw=0.5)\n",
        "    _ax_rf.set_yticks(_y)\n",
        "    _ax_rf.set_yticklabels(_pi_rf_pretty.index, fontsize=10)\n",
        "    _ax_rf.invert_yaxis()\n",
        "    _ax_rf.axvline(0, color='black', lw=0.8)\n",
        "    _ax_rf.set_xlabel('Permutation importance', fontsize=10)\n",
        "    _ax_rf.set_title(f'RF \u2014 {_tgt_label}', fontsize=11)\n",
        "    _ax_rf.spines[['top', 'right']].set_visible(False)\n",
        "    _auc_rf = refit_results[('RF', _tgt)][1]['cv']['auc']\n",
        "    _ax_rf.text(0.98, 0.02, f'CV AUC: {_auc_rf[0]:.3f} \u00b1 {_auc_rf[1]:.3f}',\n",
        "               transform=_ax_rf.transAxes, ha='right', va='bottom', fontsize=9,\n",
        "               bbox=dict(boxstyle='round', facecolor='white', alpha=0.85))\n",
        "\n",
        "    # Row 1: Logistic |coefficient|\n",
        "    _ax_lr = axes3[1, col_idx]\n",
        "    _pipe_lr = refit_results[('Logistic', _tgt)][0]\n",
        "    _coef_imp = _logistic_coef_importance(_pipe_lr, _sel_preds, treat_as).head(_N_FEAT)\n",
        "    _coef_pretty = _coef_imp.rename(index=lambda x: _clean_predictor_name(x))\n",
        "    _y2 = np.arange(len(_coef_pretty))\n",
        "    _ax_lr.barh(_y2, _coef_pretty.values, color=_clr, alpha=0.65,\n",
        "                edgecolor='white', lw=0.5)\n",
        "    _ax_lr.set_yticks(_y2)\n",
        "    _ax_lr.set_yticklabels(_coef_pretty.index, fontsize=10)\n",
        "    _ax_lr.invert_yaxis()\n",
        "    _ax_lr.axvline(0, color='black', lw=0.8)\n",
        "    _ax_lr.set_xlabel('|Standardised coefficient|', fontsize=10)\n",
        "    _ax_lr.set_title(f'Logistic \u2014 {_tgt_label}', fontsize=11)\n",
        "    _ax_lr.spines[['top', 'right']].set_visible(False)\n",
        "    _auc_lr = refit_results[('Logistic', _tgt)][1]['cv']['auc']\n",
        "    _ax_lr.text(0.98, 0.02, f'CV AUC: {_auc_lr[0]:.3f} \u00b1 {_auc_lr[1]:.3f}',\n",
        "               transform=_ax_lr.transAxes, ha='right', va='bottom', fontsize=9,\n",
        "               bbox=dict(boxstyle='round', facecolor='white', alpha=0.85))\n",
        "\n",
        "fig3.suptitle('Feature importance: RF permutation vs Logistic |coefficient|',\n",
        "              fontsize=13, fontweight='normal', y=1.01)\n",
        "plt.tight_layout()\n",
        "plt.show()"
    ]
})

# ═══════════════════════════════════════════════════════════════════
# Cell 17: save & register
# ═══════════════════════════════════════════════════════════════════
cells.append({
    "cell_type": "code",
    "metadata": {},
    "outputs": [],
    "execution_count": None,
    "source": [
        "# \u2500\u2500 12. Save figures and register \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n",
        "_fig_dir = os.path.join('..', 'figures', 'outcomes')\n",
        "os.makedirs(_fig_dir, exist_ok=True)\n",
        "\n",
        "# Save Fig 1: baseline scenario sweep\n",
        "_name1 = 'fig_model_comparison_scenarios.png'\n",
        "fig1.savefig(os.path.join(_fig_dir, _name1), dpi=300, bbox_inches='tight')\n",
        "\n",
        "_all_intact_rf  = baseline_results.get(('all_predictors', 'RF', 'Intact'), (None, {'cv': {'auc': (np.nan, np.nan)}}))[1]['cv']['auc']\n",
        "_all_intact_lr  = baseline_results.get(('all_predictors', 'Logistic', 'Intact'), (None, {'cv': {'auc': (np.nan, np.nan)}}))[1]['cv']['auc']\n",
        "_all_eff_rf     = baseline_results.get(('all_predictors', 'RF', 'Effective'), (None, {'cv': {'auc': (np.nan, np.nan)}}))[1]['cv']['auc']\n",
        "_all_eff_lr     = baseline_results.get(('all_predictors', 'Logistic', 'Effective'), (None, {'cv': {'auc': (np.nan, np.nan)}}))[1]['cv']['auc']\n",
        "\n",
        "register_outcomes_figure(\n",
        "    'fig_model_comparison_scenarios',\n",
        "    'Model comparison \\u2014 scenario sweep',\n",
        "    _name1,\n",
        "    f'Dot-plot comparing RF and Logistic L2 across four predictor scenarios for both outcomes. '\n",
        "    f'All-predictors: Condition RF AUC {_all_intact_rf[0]:.3f} \\u00b1 {_all_intact_rf[1]:.3f}, '\n",
        "    f'Logistic {_all_intact_lr[0]:.3f} \\u00b1 {_all_intact_lr[1]:.3f}. '\n",
        "    f'Veg response RF AUC {_all_eff_rf[0]:.3f} \\u00b1 {_all_eff_rf[1]:.3f}, '\n",
        "    f'Logistic {_all_eff_lr[0]:.3f} \\u00b1 {_all_eff_lr[1]:.3f}.',\n",
        "    f'RF and Logistic L2 compared across 4 predictor scenarios. '\n",
        "    f'All-predictors condition AUC: RF {_all_intact_rf[0]:.3f}, Logistic {_all_intact_lr[0]:.3f}.'\n",
        ")\n",
        "print(f'Saved: {_name1}')\n",
        "\n",
        "# Save Fig 2: before vs after feature selection\n",
        "_name2 = 'fig_rfecv_feature_selection.png'\n",
        "fig2.savefig(os.path.join(_fig_dir, _name2), dpi=300, bbox_inches='tight')\n",
        "\n",
        "_n_sel_int = len(rfecv_results['Intact']['selected_predictors'])\n",
        "_n_sel_eff = len(rfecv_results['Effective']['selected_predictors'])\n",
        "\n",
        "register_outcomes_figure(\n",
        "    'fig_rfecv_feature_selection',\n",
        "    'RFECV feature selection effect',\n",
        "    _name2,\n",
        "    f'Bar chart showing CV AUC before (all {len(_all_preds)} predictors) and after RFECV selection. '\n",
        "    f'Condition: RFECV selected {_n_sel_int} predictors. '\n",
        "    f'Veg response: RFECV selected {_n_sel_eff} predictors.',\n",
        "    f'RFECV reduces predictors ({len(_all_preds)} \\u2192 {_n_sel_int} for condition, '\n",
        "    f'{_n_sel_eff} for veg response) with minimal AUC change.'\n",
        ")\n",
        "print(f'Saved: {_name2}')\n",
        "\n",
        "# Save Fig 3: feature importance\n",
        "_name3 = 'fig_model_feature_importance.png'\n",
        "fig3.savefig(os.path.join(_fig_dir, _name3), dpi=300, bbox_inches='tight')\n",
        "\n",
        "_top_rf_int = ', '.join(refit_results[('RF', 'Intact')][2].head(3).index.tolist())\n",
        "_top_rf_eff = ', '.join(refit_results[('RF', 'Effective')][2].head(3).index.tolist())\n",
        "\n",
        "register_outcomes_figure(\n",
        "    'fig_model_feature_importance',\n",
        "    'Feature importance \\u2014 RF vs Logistic',\n",
        "    _name3,\n",
        "    f'2\\u00d72 feature importance panel: RF permutation importance (top) and '\n",
        "    f'Logistic |coefficient| (bottom) for Condition and Veg response. '\n",
        "    f'Top RF predictors for Condition: {_top_rf_int}. '\n",
        "    f'Top RF predictors for Veg response: {_top_rf_eff}.',\n",
        "    f'RF vs Logistic feature importance: top condition predictors are {_top_rf_int}; '\n",
        "    f'top veg response predictors are {_top_rf_eff}.'\n",
        ")\n",
        "print(f'Saved: {_name3}')\n",
        "\n",
        "print('\\nAll figures saved and registered.')"
    ]
})

# ═══════════════════════════════════════════════════════════════════
# Write notebook
# ═══════════════════════════════════════════════════════════════════
nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "berm-venv",
            "language": "python",
            "name": "berm-venv"
        },
        "language_info": {
            "name": "python",
            "version": "3.11.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

with open(NB_PATH, "w") as f:
    json.dump(nb, f, indent=1)

print(f"Wrote {len(cells)} cells to {NB_PATH}")
