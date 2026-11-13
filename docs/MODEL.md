# Model notes

This file has the equations, the parameter values, and where each value comes from. Time is in seconds. The
stimulus R(t) is a square pulse in firing rate (20 Hz from t = 3 s to t = 5 s unless I say otherwise).

The model is a chain, nothing feeds back:

```
R(t) -> V (vesicles) -> G (glutamate) -> I (IP3) -> C (Ca2+) -> s -> f (flow) -> v, q -> BOLD
        synapse         extracellular    astrocyte               hemodynamics
```

## Equations

Synapse and glutamate pool. Vesicle depression follows the rate-based form of Tsodyks and Markram (1997).
Uptake is a Michaelis-Menten term.

$$\dot V = \frac{1-V}{\tau_{rec}} - U\,R\,V \qquad
\dot G = \rho\,U\,R\,V - \frac{V_{max}\,G}{K_m + G}$$

Astrocyte. This part is phenomenological (saturating production of IP3, then a saturating Ca2+ release term
with first-order decay). It is not a copy of a specific published astrocyte model.

$$\dot I = k_{prod}\frac{G}{K_G+G} - k_{deg} I \qquad
\dot C = J_{max}\frac{I^2}{I^2+K_I^2} - \frac{C}{\tau_{Ca}}$$

Hemodynamics. Flow-inducing signal and Balloon model as in Friston et al. (2000), with the Balloon model of
Buxton et al. (1998).

$$\dot s = \epsilon C - \kappa s - \gamma (f-1) \qquad \dot f = s$$
$$\tau_0 \dot v = f - v^{1/\alpha} \qquad
\tau_0 \dot q = f\,\frac{E(f)}{E_0} - q\,v^{(1-\alpha)/\alpha},\quad E(f)=1-(1-E_0)^{1/f}$$

BOLD signal (`core.solver.bold_signal`), same form as in Buxton et al. (2004) and Stephan et al. (2007):

$$\text{BOLD}\,[\%] = 100\,V_0\left[k_1(1-q) + k_2\left(1-\tfrac{q}{v}\right) + k_3(1-v)\right]$$

with k1 = 7 E0, k2 = 2, k3 = 0.2 and V0 = 0.04 in my code (see the notes under the table).

Start values: V = 1, G = I = C = s = 0, f = v = q = 1. With no stimulus nothing moves away from this, which Exp 0
and the tests check.

## Parameters and sources

I checked each value against the literature. "Matches" means I found the same number in the cited paper,
"same range" means the value is in the range reported but is not copied from it, and "no source" means I did not
find a published value, so it is a free (phenomenological) parameter.

| Parameter | Value | Meaning | Status | Source |
|---|---|---|---|---|
| `tau_rec` | 0.8 s | vesicle recovery time | matches | Tsodyks & Markram 1997 (tau_rec = 800 ms for their example synapse) |
| `U` | 0.4 | release probability | same range | Tsodyks & Markram 1997 use U_SE = 0.67 and 0.55 in their examples; 0.4 is somewhat lower |
| `K_m` | 15 uM | uptake half-saturation | same range | Arriza et al. 1994: EAAT K_m = 18-28 uM in oocytes, 48-97 uM in mammalian cells |
| `kappa` | 0.65 /s | signal decay | matches | Friston et al. 2003; Stephan et al. 2007 (DCM prior mean) |
| `gamma` | 0.41 /s | flow-dependent feedback | matches | Friston et al. 2003; Stephan et al. 2007 (DCM prior mean) |
| `tau_0` | 0.98 s | mean transit time | matches | Friston et al. 2003; Stephan et al. 2007 (DCM prior mean) |
| `alpha` | 0.33 | Grubb exponent | nearly | DCM prior mean is 0.32; the exponent comes from Grubb et al. 1974 |
| `E_0` | 0.4 | resting oxygen extraction | differs | DCM prior mean is 0.34 (Friston et al. 2003); I used 0.4 |
| `epsilon` | 0.1 | gain from Ca2+ to vasodilatory signal | no source | in Friston et al. 2000 this is a free efficacy parameter |
| `rho` | 250 | glutamate released per unit vesicle release | no source | |
| `V_max` | 50 uM/s | maximal uptake rate | no source | |
| `K_G` | 10 uM | glutamate level for half-maximal IP3 production | no source | |
| `k_prod` | 0.5 uM/s | maximal IP3 production | no source | |
| `k_deg` | 2.0 /s | IP3 degradation rate | no source | |
| `J_max` | 20 uM/s | maximal Ca2+ release | no source | |
| `K_I` | 2.0 uM | IP3 level for half-maximal Ca2+ release | no source | |
| `tau_Ca` | 3.0 s | Ca2+ decay time | no source | |

BOLD constants (fixed in `solver.py`):

| Constant | Value in code | Value in literature | Effect of switching |
|---|---|---|---|
| `V0` | 0.04 | 0.02 (Friston et al. 2000, at 1.5 T) | halves the BOLD amplitude (peak 1.98 % -> 0.99 %) |
| `k1` | 7 E0 | 7 E0 (Buxton et al. 2004) | none |
| `k2` | 2 | 2 (Buxton et al. 2004) | none |
| `k3` | 0.2 | 2 E0 - 0.2 = 0.6 for E0 = 0.4 (Buxton et al. 2004) | lowers the peak by about 5 % (1.98 % -> 1.88 %) |

Neither of these changes the shape or timing of the BOLD curve, only its size. Because of this, the BOLD
percentages in this repository should be read as model units and not compared directly with measured fMRI
amplitudes. The code keeps the values I originally used; the table above shows how they differ from the papers.

The uptake parameter `V_max` and the release scale `rho` are the ones that matter most for the problems described
in the README (very large glutamate values and slow clearance), and they have no source at all.

## Numerics

`scipy.integrate.solve_ivp` with rtol = 1e-5, atol = 1e-7 and max_step = 0.01 s. The small max_step is there so
the adaptive solver cannot step over a short stimulus pulse (there is a test for this). RK45 and Radau agree to
about 1.6e-4 % BOLD in Exp 0.

## References

See the reference list in the main README.
