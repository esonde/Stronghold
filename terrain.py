
import numpy as np

def generate_terrain(n: int, smooth_steps: int = 4, seed: int | None = None) -> np.ndarray:
    """
    Genera una mappa altimetrica nxn in [0,1] con variazioni naturali.
    smooth_steps controlla quante volte viene applicato un blur semplice.
    """
    rng = np.random.default_rng(seed)
    terrain = rng.random((n, n), dtype=np.float32)

    # Smooth per ridurre il gradiente locale
    kernel = np.array([[0, 1, 0],
                       [1, 4, 1],
                       [0, 1, 0]], dtype=np.float32) / 8.0

    for _ in range(smooth_steps):
        # pad con riflessione ai bordi
        padded = np.pad(terrain, 1, mode='edge')
        out = np.zeros_like(terrain)
        for i in range(3):
            for j in range(3):
                out += padded[i:i+n, j:j+n] * kernel[i, j]
        terrain = out

    # accentua zone alte e basse per avere più acqua e rilievi
    terrain = np.clip(terrain ** 1.5, 0.0, 1.0)
    return terrain
