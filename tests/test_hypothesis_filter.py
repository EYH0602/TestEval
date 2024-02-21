from src.static import is_property_based
import ast
from src.navigate import ModuleNavigator, find_all


def _code_helper(code: str, expected: bool = True):
    root = ast.parse(code)
    funcs = find_all(root, ast.FunctionDef)
    assert len(funcs) == 1
    func = funcs[0]
    assert is_property_based(func) == expected


def test_numpy():
    code = """
@hypothesis.given(
        arr=arrays(dtype=np.float64,
                   shape=st.integers(min_value=3, max_value=1000),
                   elements=st.floats(allow_infinity=False, allow_nan=False,
                                      min_value=-1e300, max_value=1e300)))
def test_quantile_monotonic_hypo(self, arr):
    p0 = np.arange(0, 1, 0.01)
    quantile = np.quantile(arr, p0)
    assert_equal(np.sort(quantile), quantile)
"""
    _code_helper(code, True)

    code = """
@pytest.mark.parametrize("func", [xp.unique_all, xp.unique_inverse])
@given(xps.arrays(dtype=xps.scalar_dtypes(), shape=xps.array_shapes()))
def test_inverse_indices_shape(func, x):
    out = func(x)
    assert out.inverse_indices.shape == x.shape
"""
    _code_helper(code, True)


def test_regular():
    code = """
@pytest.mark.parametrize("method", methods_supporting_weights)
def test_quantile_with_weights_and_axis(self, method):
    rng = np.random.default_rng(4321)

    # 1d weight and single alpha
    y = rng.random((2, 10, 3))
    w = np.abs(rng.random(10))
    alpha = 0.5
    q = np.quantile(y, alpha, weights=w, method=method, axis=1)
    q_res = np.zeros(shape=(2, 3))
    for i in range(2):
        for j in range(3):
            q_res[i, j] = np.quantile(
                y[i, :, j], alpha, method=method, weights=w
            )
    assert_allclose(q, q_res)
"""
    _code_helper(code, False)


if __name__ == "__main__":
    test_numpy()
    test_regular()
