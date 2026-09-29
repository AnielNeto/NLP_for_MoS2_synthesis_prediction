# CÓDIGO MAJORITARIAMENTE CRIADO POR LLM

import numpy as np
from sklearn.model_selection import KFold
from cca_zoo.sparse import IPLSCCA


def fit_scca_ipls(X, Y, alpha, l1_ratio=0.0, latent_dimensions=5):
    modelo = IPLSCCA(
        latent_dimensions=latent_dimensions,
        alpha=[alpha, alpha],
        l1_ratio=[l1_ratio, l1_ratio],
    )
    modelo.fit([X, Y])
    return modelo

def evaluate_correlation(modelo, X, Y, dim=0):
    x_scores, y_scores = modelo.transform([X, Y])
    return np.corrcoef(x_scores[:, dim], y_scores[:, dim])[0, 1]


def nested_cv_scca_ipls(X, Y, alphas, n_outer=5, n_inner=5, l1_ratio=0.0, random_state=639, _dim=0):
    """
    Loop externo: estima correlação canônica em dados nunca vistos.
    Loop interno: escolhe alpha usando só o treino do fold externo.
    """
    outer_cv = KFold(n_splits=n_outer, shuffle=True, random_state=random_state)
    inner_cv = KFold(n_splits=n_inner, shuffle=True, random_state=random_state)
    resultados = []

    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        Y_train, Y_test = Y[train_idx], Y[test_idx]

        melhor_score = -np.inf
        melhor_alpha = None

        for alpha in alphas:
            scores_inner = []
            for itr_idx, ival_idx in inner_cv.split(X_train):
                X_itr, X_ival = X_train[itr_idx], X_train[ival_idx]
                Y_itr, Y_ival = Y_train[itr_idx], Y_train[ival_idx]

                modelo = fit_scca_ipls(X_itr, Y_itr, alpha, l1_ratio)
                scores_inner.append(evaluate_correlation(modelo, X_ival, Y_ival, dim=_dim))

            score_medio = np.mean(scores_inner)
            if score_medio > melhor_score:
                melhor_score = score_medio
                melhor_alpha = alpha

        modelo_final = fit_scca_ipls(X_train, Y_train, melhor_alpha, l1_ratio)
        corr_train = evaluate_correlation(modelo_final, X_train, Y_train, dim=_dim)
        corr_test = evaluate_correlation(modelo_final, X_test, Y_test, dim=_dim)

        resultados.append({
            "fold": fold_idx,
            "alpha": melhor_alpha,
            "corr_train": corr_train,
            "corr_test": corr_test,
        })

    return resultados

    
def pipeline_completo(X, Y, alphas, n_inner=5, l1_ratio=0.0, random_state=0, _dim=0):
    """Roda CV interna pra escolher alpha, ajusta modelo final, retorna rho[0]."""
    inner_cv = KFold(n_splits=n_inner, shuffle=True, random_state=random_state)
    melhor_score = -np.inf
    melhor_alpha = None

    for alpha in alphas:
        scores = []
        for itr_idx, ival_idx in inner_cv.split(X):
            modelo = fit_scca_ipls(X[itr_idx], Y[itr_idx], alpha, l1_ratio)
            scores.append(evaluate_correlation(modelo, X[ival_idx], Y[ival_idx], dim=_dim))
        score_medio = np.mean(scores)
        if score_medio > melhor_score:
            melhor_score = score_medio
            melhor_alpha = alpha

    modelo_final = fit_scca_ipls(X, Y, melhor_alpha, l1_ratio)
    return evaluate_correlation(modelo_final, X, Y, dim=_dim)


def teste_permutacao(X, Y, alphas, B=500, l1_ratio=0.0, random_state=0, __dim=0):
    rng = np.random.default_rng(random_state)

    rho_obs = pipeline_completo(X, Y, alphas, random_state=random_state, _dim=__dim)

    rho_permutados = np.empty(B)
    for b in range(B):
        Y_perm = rng.permutation(Y, axis=0)
        rho_permutados[b] = pipeline_completo(X, Y_perm, alphas, random_state=random_state + b, _dim=__dim)

        print("Round:", b)

    p_valor = (np.sum(rho_permutados >= rho_obs) + 1) / (B + 1)

    return {"rho_obs": rho_obs, "rho_permutados": rho_permutados, "p_valor": p_valor}