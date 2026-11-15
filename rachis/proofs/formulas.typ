// Formulas of every kind in a paragraph and in displays: what a mathematics font is read in.
//
//   typst compile --font-path fonts/ttf --input math="Rachis Math" proofs/formulas.typ formulas.png --ppi 200
//
// from `rachis/`, after `rachis build`. Another mathematics font is named the same way, to set the sheet beside it
// (`--font-path` its directory). Characters the font lacks are set in New Computer Modern Math, which Typst carries.
#let mathfont = sys.inputs.at("math", default: "New Computer Modern Math")
#let textfont = sys.inputs.at("text", default: "Rachis")
#set page(width: 170mm, height: auto, margin: 9mm)
#set text(font: textfont, size: 10pt)
#show math.equation: set text(font: (mathfont, "New Computer Modern Math"))
#set par(justify: true)
#text(size: 8pt, fill: gray)[mathematics: #mathfont · text: #textfont]

Let $(X, d)$ be a compact metric space and $f: X -> RR$ continuous. For every $epsilon > 0$ there is $delta > 0$ such that $d(x, y) < delta$ implies $|f(x) - f(y)| < epsilon$. The eigenvalues $lambda_1 >= lambda_2 >= dots >= lambda_n$ of $A^top A$ are the squares $sigma_i^2$ of the singular values, so $norm(A)_2 = sigma_1$. If $p or q$ and $not p$ then $q$; the density $rho$ and the pressure $p$ satisfy $partial_t rho + nabla dot (rho bold(u)) = 0$, and $x in A subset.eq B$, $forall x exists y$, $a^2 + b^2 = c^2$, $e^(i pi) + 1 = 0$, $f'(x)$, $x_(i j)^(2 k)$, $n!$, $binom(n, k)$.

$ sum_(n=0)^infinity a_n x^n = integral_0^1 f(x) dif x, quad product_(k=1)^n (1 + 1/k), quad lim_(x -> 0) (sin x)/x = 1, quad union.big_(i in I) U_i supset.eq K $
$ x = (-b plus.minus sqrt(b^2 - 4 a c)) / (2 a), quad sqrt(1 + sqrt(1 + sqrt(1 + x))), quad root(3, x/y), quad (a/b)/(c/d), quad 1/(1 + 1/(1 + 1/x)) $
$ mat(a, b; c, d) vec(x, y) = vec(a x + b y, c x + d y), quad mat(delim: "[", 1, 0, 0; 0, 1, 0; 0, 0, 1), quad det mat(delim: "|", a, b; c, d) = a d - b c, quad f(x) = cases(x^2 & "if" x >= 0, -x & "otherwise") $
$ (integral_a^b f)^2 <= (b - a) integral_a^b f^2, quad [sum_(i=1)^n x_i^2]^(1/2), quad {x in RR : abs(x) < 1}, quad lr(⟨u, v⟩), quad norm(sum_i x_i), quad floor(x/2) + ceil(y/2) $
$ hat(x), tilde(y), macron(z), dot(x), dot.double(x), arrow(v), hat(A), tilde(B), overline(a + b), underline(c d), overbrace(a + dots + a, n), underbrace(x y z, 3), accent(f, hat) $
$ A arrow.r.long B arrow.r.double C arrow.l.r D mapsto E, quad X stretch(->)^(f compose g) Y, quad a approx b equiv c tilde d prop e != f, quad a times b div c dot d ⊕ e ⊗ f $
$ alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi pi rho sigma tau upsilon phi chi psi omega quad Gamma Delta Theta Lambda Xi Pi Sigma Phi Psi Omega quad epsilon.alt theta.alt phi.alt rho.alt $
$ a b c d e f g h i j k l m n o p q r s t u v w x y z quad A B C D E F G H I J K L M N O P Q R S T U V W X Y Z quad 0 1 2 3 4 5 6 7 8 9 $
$ bold(a b c x y z A B C) quad upright(a b c x y z) quad bb(A B C N Z Q R C) quad cal(A B C L) quad frak(g h A) quad sans(a b A B) quad mono(a b A B) quad bold(alpha beta Gamma) $
$ e^(x^(y^z)), quad a_(i_(j_k)), quad x^2_i + y^3_j, quad f^((n))(x), quad integral.double_D, quad integral.cont_gamma, quad sum_(i < j), quad lim_(n -> infinity) sup_(k >= n) a_k, quad partial^2 / (partial x partial y) $
