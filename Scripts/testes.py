# CÓDIGO MAJORITARIAMENTE CRIADO POR LLM

import numpy as np
import scipy.stats as stats

from typing import Tuple

def mardia_test(data: np.ndarray, cov: bool = True) -> Tuple[float, float, float, float]:
    """
    https://rdrr.io/cran/MVN/src/R/mvn.R
    https://stats.stackexchange.com/questions/317147/how-to-get-a-single-p-value-from-the-two-p-values-of-a-mardias-multinormality-t
    Mardia's multivariate skewness and kurtosis.
    Calculates the Mardia's multivariate skewness and kurtosis coefficients
    as well as their corresponding statistical test. For large sample size
    the multivariate skewness is asymptotically distributed as a Chi-square
    random variable; here it is corrected for small sample size. However,
    both uncorrected and corrected skewness statistic are presented. Likewise,
    the multivariate kurtosis it is distributed as a unit-normal.

     Syntax: function [Mskekur] = Mskekur(X,c,alpha)

     Inputs:
          X - multivariate data matrix [Size of matrix must be n(data)-by-p(variables)].
          cov - boolean to whether to normalize the covariance matrix by n (c=1[default]) or by n-1 (c~=1)

     Outputs:
          - skewness test statistic
          - kurtosis test statistic
          - significance value for skewness
          - significance value for kurtosis
    """
    n, p = data.shape

    # correct for small sample size
    small: bool = True if n < 20 else False

    if cov:
        S = ((n - 1)/n) * np.cov(data.T)
    else:
        S = np.cov(data.T)

    # calculate mean
    data_mean = data.mean(axis=0)
    # inverse - check if singular matrix
    try:
        iS = np.linalg.inv(S)
    except Exception as e:
        # print for now
        print(e)
        return 0.0, 0.0, 0.0, 0.0
    # squared-Mahalanobis' distances matrix
    D: np.ndarray = (data - data_mean) @ iS @ (data - data_mean).T
    # multivariate skewness coefficient
    g1p: float = np.sum(D**3)/n**2
    # multivariate kurtosis coefficient
    g2p: float = np.trace(D**2)/n
    # small sample correction
    k: float = ((p + 1)*(n + 1)*(n + 3))/(n*(((n + 1)*(p + 1)) - 6))
    # degrees of freedom
    df: float = (p * (p + 1) * (p + 2))/6

    if small:
        # skewness test statistic corrected for small sample: it approximates to a chi-square distribution
        g_skew = (n * g1p * k)/6
    else:
        # skewness test statistic:it approximates to a chi-square distribution
        g_skew = (n * g1p)/6

    # significance value associated to the skewness corrected for small sample
    p_skew = stats.chi2.sf(g_skew, df)

    # kurtosis test statistic: it approximates to a unit-normal distribution
    g_kurt = (g2p - (p*(p + 2)))/(np.sqrt((8 * p * (p + 2))/n))
    # significance value associated to the kurtosis
    p_kurt = 2 * stats.norm.sf(np.abs(g_kurt))

    return g_skew, g_kurt, p_skew, p_kurt


def pillai_test(rho: np.ndarray, N: int, p: int, q: int, rhostart: int = 1):
    """
    Teste F aproximado para a Pillai-Bartlett Trace, equivalente a
    CCP::p.asym(rho, N, p, q, tstat="Pillai") do R.

    rho       : correlações canônicas, ordenadas decrescente (rho[0] = maior)
    N         : número de observações
    p, q      : número de variáveis em cada bloco (X e Y)
    rhostart  : índice (1-based) da primeira correlação incluída no teste.
                rhostart=1 testa todas; rhostart=2 exclui rho[0]; etc.
                (equivalente ao "k" das dimensões já extraídas)
    """
    k = rhostart - 1          # índice 0-based da primeira correlação testada
    m = min(p, q)             # total de correlações canônicas possíveis
    rho_k = rho[k:m]          # correlações remanescentes neste teste

    p1 = p - k
    q1 = q - k
    s  = min(p1, q1)          # número de correlações no subteste atual

    # estatística de Pillai: soma das correlações canônicas ao quadrado
    V = np.sum(rho_k ** 2)

    m_ = (abs(p1 - q1) - 1) / 2
    n_ = (N - k - p1 - q1 - 1) / 2

    df1 = s * (2 * m_ + s + 1)
    df2 = s * (2 * n_ + s + 1)

    F = ((2 * n_ + s + 1) / (2 * m_ + s + 1)) * (V / (s - V))

    p_value = stats.f.sf(F, df1, df2)

    return {"statistic": V, "F": F, "df1": df1, "df2": df2, "p_value": p_value}