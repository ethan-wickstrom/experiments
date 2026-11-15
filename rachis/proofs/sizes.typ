// Everything that grows: delimiters, radicals, display operators, accents, braces and arrows at many sizes.
//
//   typst compile --font-path fonts/ttf --input math="Rachis Math" proofs/sizes.typ sizes.png --ppi 200
//
// from `rachis/`, after `rachis build`. Another mathematics font is named the same way, to set the sheet beside it
// (`--font-path` its directory). Characters the font lacks are set in New Computer Modern Math, which Typst carries.
#let mathfont = sys.inputs.at("math", default: "New Computer Modern Math")
#let textfont = sys.inputs.at("text", default: "Rachis")
#set page(width: 190mm, height: auto, margin: 8mm)
#set text(font: textfont, size: 10pt)
#show math.equation: set text(font: (mathfont, "New Computer Modern Math"))
#let col(n) = range(n).map(i => $#(i + 1)$)
#let tower(d, n) = math.vec(delim: d, ..col(n))
$ #tower("(", 1) #tower("(", 2) #tower("(", 3) #tower("(", 4) #tower("(", 5) #tower("(", 6) #tower("(", 7) #tower("(", 9) #tower("(", 12) quad #tower("[", 2) #tower("[", 4) #tower("[", 7) #tower("[", 12) quad #tower("{", 2) #tower("{", 4) #tower("{", 7) #tower("{", 12) quad #tower("|", 3) #tower("|", 12) #tower("‖", 3) #tower("‖", 9) $
$ lr(⟨ #math.vec(delim: none, ..col(4)) ⟩) quad lr(⟨ #math.vec(delim: none, ..col(8)) ⟩) quad lr(⌊ #math.vec(delim: none, ..col(3)) ⌋) quad lr(⌈ #math.vec(delim: none, ..col(8)) ⌉) quad lr(⌊ #math.vec(delim: none, ..col(12)) ⌋) quad lr(⟦ #math.vec(delim: none, ..col(5)) ⟧) $
$ sqrt(x) sqrt(x^2) sqrt(a/b) sqrt(#math.vec(delim: none, ..col(3))) sqrt(#math.vec(delim: none, ..col(5))) sqrt(#math.vec(delim: none, ..col(8))) quad sqrt(1 + sqrt(2 + sqrt(3 + sqrt(4 + x)))) quad root(n, a_1 a_2 dots.c a_n) quad root(3, (x^2 + y^2)/(1 + z^2)) $
$ sum_(i=1)^n product_(j=1)^m union.big_(k) inter.big_k union.sq.big_k or.big_i and.big_i ⨁_i ⨂_i ⨀_i product.co_i integral_0^infinity integral.double_Omega integral.triple_V integral.cont_gamma quad integral_(-infinity)^infinity e^(-x^2) dif x = sqrt(pi) $
$ hat(a) hat(a b) hat(a b c) hat(a b c d e) hat(a b c d e f g h) quad tilde(a) tilde(a b) tilde(a b c d) tilde(a b c d e f g) quad overline(a) arrow(a) arrow(A B) arrow(A B C D) arrow(A B C D E F G) quad accent(a b c, macron) $
$ overbrace(a + b, 2) overbrace(a + b + c + d, 4) overbrace(a_1 + a_2 + a_3 + dots.c + a_(n-1) + a_n, n "terms") quad underbrace(x + y + z + w + u + v, 6) quad overbracket(a + b + c + d) underbracket(a + b + c + d + e + f) $
$ A stretch(->)^("f") B stretch(->)^("a long label here") C stretch(<-)_("back") D stretch(=>)^("implies that") E stretch(<=>)^("if and only if") F stretch(|->)^(x |-> x^2) G stretch(=)^("def") H stretch(harpoons.rtlb)^("react") I $
$ x^(a^(b^c)) quad x_(a_(b_c)) quad 2^(2^(2^2)) quad e^(-(x - mu)^2 / (2 sigma^2)) quad a^(n+1)_(i j) quad sum_(k=0)^n binom(n, k) x^k y^(n-k) quad lim_(h -> 0) (f(x + h) - f(x))/h quad nabla times bold(E) = -(partial bold(B))/(partial t) $
$ integral_0^1 (f(x))/(g(x)) dif x = sum_(n=1)^infinity (a_n)/(b_n) = product_(p "prime") 1/(1 - p^(-s)), quad integral.double_D (partial Q)/(partial x) - (partial P)/(partial y) dif A = integral.cont_(partial D) P dif x + Q dif y, quad union.big_(i=1)^n A_i $
$ overbrace(x) quad underbrace(y) quad overbrace(x y) quad overbrace(x y z) quad overparen(a b c) quad underparen(x y z) quad overshell(a + b + c) quad undershell(p + q + r, 3) quad overparen(a_1 + a_2 + dots.c + a_n) quad underparen(x + y + z + w, 4) $
$ underbrace(a_1 + a_2 + a_3 + a_4 + a_5 + a_6 + a_7 + a_8 + a_9 + a_10 + a_11 + a_12 + a_13 + a_14, "fourteen terms in all") $
$ A stretch(<->)^"both ways" B stretch(arrow.hook)^"into" C stretch(->>)^"onto" D stretch(arrows.rr)^"two of them" E stretch(arrows.rl)^"there and back" F stretch(<==)^"is implied by" G stretch(arrow.l.bar)^"from" H stretch(arrow.r.tail)^"one to one" I stretch(harpoon.rt)^"half" J stretch(arrow.squiggly)^"wave" K $
