"""Linear readout of nonlinear cross-encoder differences."""
import torch
import torch.nn.functional as F

FULL = ("first_final", "first_goal_state", "first_goal_logp", "first_checks_logp",
        "first_margin", "comparison")
REGULARIZATION = 0.1
TIE = 1e-8


def train(rows, signs, keys):
    # Normalize whole feature groups by the RMS pair length in the training
    # families. No offsets: swapping candidates must negate the exact score.
    matrices = {k: torch.stack([r[k] for r in rows]).double() for k in keys}
    scales = {k: x.square().sum(1).mean().sqrt().clamp_min(1e-8) for k, x in matrices.items()}
    x = torch.cat([matrices[k] / scales[k] for k in keys], dim=1)
    signed = x * torch.tensor(signs, dtype=x.dtype)[:, None]
    reversals = (signed[::2] + signed[1::2]) / 2
    weight = torch.zeros(x.shape[1], dtype=x.dtype, requires_grad=True)
    optimizer = torch.optim.LBFGS([weight], max_iter=100, tolerance_grad=1e-9,
                                  tolerance_change=1e-12, line_search_fn="strong_wolfe")

    def closure():
        optimizer.zero_grad()
        loss = (F.softplus(-(signed @ weight)).mean() + F.softplus(-(reversals @ weight)).mean()) / 2
        loss = loss + REGULARIZATION * weight.square().sum() / 2
        loss.backward()
        return loss

    optimizer.step(closure)
    # Fold scales into the coefficients for use on raw feature differences.
    groups = weight.detach().split([matrices[k].shape[1] for k in keys])
    return {k: (w / scales[k]).contiguous() for k, w in zip(keys, groups, strict=True)}


def score(features, head):
    return sum(float(torch.dot(features[k].double(), v)) for k, v in head.items())


def response(margin):
    return {"scores": [margin / 2, -margin / 2],
            "choice": (0 if margin > 0 else 1) if abs(margin) > TIE else None}
