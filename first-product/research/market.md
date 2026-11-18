# Selling a paid Mac app / developer tool by direct download: verified facts as of 2026-10-15

All pages were read on 2026-10-15 unless another date is given.

**Source flags used on every number**

- **[checked]**: I read it myself on the primary page (vendor pricing page, vendor docs, Apple developer docs or WWDC session page, court docket, founder's own page).
- **[checked-mirror]**: I read the primary text through a mirror because the original host blocked my fetch. Examples: a Reddit post read on a redlib mirror, a court filing PDF hosted by 9to5Mac, and Apple's `fm(1)` man page mirrored from Xcode.
- **[secondhand]**: news articles, aggregators, competitor blogs, or third-party reviews. Treat these as directional only.
- **[computed]**: my own arithmetic on checked inputs, or my own queries against a public API.
- **[analysis]**: my judgment. These are not facts.

---

## 0. Bottom line

**Recommended path for the first sale within days:** sell direct with **Polar** as the merchant of record, and use Polar's built-in license keys.

- **Fee:** 5% + 50¢ per transaction, plus 1.5% on non-US cards. **[checked]** <https://polar.sh/resources/pricing>
- **License keys:** the license-key validate and activate endpoints "doesn't require authentication and can be safely used on a public client, like a desktop application." **[checked]** <https://polar.sh/docs/api-reference/customer-portal/license-keys/validate>
- **Ship and update:** a Developer ID–signed, notarized DMG, with updates through Sparkle 2.10.0. **[checked]** <https://github.com/sparkle-project/Sparkle/releases/tag/2.10.0>
- **Fallback for a same-day start, or for card-charged-at-release pre-orders:** Gumroad, at 10% + 50¢. It has native license keys and pre-orders. **[checked]** <https://gumroad.com/pricing>
- **Avoid as a new long-term base:** Lemon Squeezy. Its owner has announced that its future is Stripe Managed Payments. **[checked]** <https://www.lemonsqueezy.com/blog/2026-update>
- **Revisit at scale:** Stripe Managed Payments. It costs 3.5% on top of 2.9% + 30¢ and has no license keys. **[checked]** <https://stripe.com/pricing>

Full reasoning is in §1.7.

---

## 1. Selling paths and fees (Oct 2026)

### 1.1 Comparison table

| Option | Merchant of record (MoR)? | Headline fee | Extras | Payouts | License keys | Pre-order / deposit support |
|---|---|---|---|---|---|---|
| **Paddle** (Billing) | Yes **[checked]** | 5% + 50¢ per checkout transaction **[checked]**. Under $10: "contact us for bespoke pricing" **[checked]** | "No monthly fees, migration fees, or hidden extras" **[checked]** | Monthly; sent by the 15th; minimum threshold $100 (adjustable to $100,000); wire or Payoneer; $15 SWIFT fee in some countries **[checked]** | **Not built in.** Paddle Billing says "you'll need to build this yourself." Use webhooks plus Keygen or your own server **[checked]** | No native pre-orders found. You can charge and refund (fee policy on refunds not checked) |
| **Polar** | Yes **[checked]** | Starter (free plan) 5% + 50¢. Pro ($20/mo) 3.8% + 40¢. Growth ($100/mo) 3.6% + 35¢. Scale ($400/mo) 3.4% + 30¢. Organizations created on or after 2026-05-27 start on Starter **[checked]** | +1.5% on non-US cards. Disputes $15. Stripe payout fees: $2 per month with active payouts, plus 0.25% + $0.25 per payout, plus 0.25%–1% FX **[checked]** | Stripe Connect Express. Review before first payout: "can take up to 14 days" **[checked]** | **Yes.** Prefixes, expiry, activation limits and usage quotas. The validate endpoint needs no auth and is safe in desktop apps **[checked]** | No native pre-orders found. "Payment fees are not refunded" on refunds **[checked]** |
| **Lemon Squeezy** (owned by Stripe) | Yes **[checked]** | 5% + 50¢ **[checked]** | +1.5% international (non-US), +1.5% PayPal, +0.5% subscriptions, +5% on recovered abandoned carts, +3% affiliate referrals **[checked]** | Twice a month **[checked]**. Payout fees: Stripe US free, non-US 1%; PayPal US $0.50, non-US 3% capped at $30 **[checked]** | **Yes.** Built in. License API rate limit 60 requests/min; the validate example shows no API key **[checked]** | No native pre-orders found. Refunds come out "minus our platform fee" **[checked]** |
| **Stripe Managed Payments** (Stripe's MoR) | Yes; Stripe is the MoR **[checked]** | **3.5% on top of** standard fees, so 2.9% + 30¢ + 3.5% for a US card **[checked]** | +1.5% international cards; +1% FX if conversion applies; disputes $15 **[checked]** | Normal Stripe payouts | **No.** None mentioned **[checked]**. Pair with Keygen or your own server | Checkout `setup_future_usage` is supported since 2026-09-03 (saves the card during a payment) **[checked]**. A setup-only mode is not documented |
| **Stripe direct** (Checkout + Stripe Tax) | **No.** You are the seller of record **[checked]** | 2.9% + 30¢ for domestic cards **[checked]** | +1.5% international cards; +1% FX; Stripe Tax Basic 0.5% per transaction where you're registered; Tax Complete from $90/mo; Billing 0.7%; disputes $15 **[checked]** | Normal Stripe payouts | No. Use Keygen or your own server | **Best primitives.** Checkout setup mode saves a card to charge later. Manual capture holds funds for 7 days on most networks. Extended 30-day holds need IC+ pricing **[checked]**. Fees are not returned on refunds **[checked]** |
| **Gumroad** | Yes, "Since January 1, 2025" **[checked]** | **10% + 50¢** direct; **30%** on Discover marketplace sales **[checked]** | none stated | Bank deposit or PayPal; schedule not checked | **Yes.** Verify API and multi-seat licenses **[checked]** | **Native pre-orders.** The help center refers to "Pre-order confirmations" **[checked]**. Cards are charged at release per the 2013 launch description **[secondhand]** |
| **FastSpring** | Yes **[checked]** | Custom quote ("flat-rate pricing based on transaction type and your volume") **[checked]**. Typically ~5.9% + $0.95, up to 8.9% **[secondhand]** | Quote form requires a business email **[checked]** | Fees withheld before payout **[checked]** | Not mentioned on the pricing page **[checked]** | Not checked |
| **Mac App Store** (Small Business Program) | Apple | **15%** if your prior calendar year's proceeds were ≤ $1M **[checked]** | $99/yr Developer Program (needed anyway for Developer ID) | Apple | Not needed | **Pre-orders supported** on macOS 10.13.2+. Brand-new apps can set release 2–180 days after the pre-order is published **[checked]** |

**Sources**

- Paddle: <https://www.paddle.com/pricing>, <https://www.paddle.com/help/manage/get-paid/when-and-how-do-i-get-paid>, <https://developer.paddle.com/migrate/start>
- Polar: <https://polar.sh/resources/pricing>, <https://polar.sh/docs/features/benefits/license-keys>, <https://polar.sh/docs/merchant-of-record/account-reviews>, <https://polar.sh/docs/features/refunds>
- Lemon Squeezy: <https://www.lemonsqueezy.com/pricing>, <https://docs.lemonsqueezy.com/help/getting-started/fees>, <https://docs.lemonsqueezy.com/api/license-api>, <https://docs.lemonsqueezy.com/help/payments/refunds-chargebacks>
- Stripe: <https://stripe.com/pricing>, <https://docs.stripe.com/payments/managed-payments>, <https://docs.stripe.com/payments/managed-payments/changelog>, <https://docs.stripe.com/payments/place-a-hold-on-a-payment-method>, <https://docs.stripe.com/payments/extended-authorization>, <https://docs.stripe.com/refunds>
- Gumroad: <https://gumroad.com/pricing>, <https://gumroad.com/help/article/76-license-keys>, <https://gumroad.com/help/article/352-supporting-your-customers>
- FastSpring: <https://fastspring.com/pricing/>; secondhand estimate from <https://toolradar.com/tools/fastspring/pricing>
- Apple: <https://developer.apple.com/app-store/small-business-program/>, <https://developer.apple.com/app-store/pre-orders/>

### 1.2 What you net per sale [computed]

Inputs are the checked rates above. "Non-US" means a non-US card. Payout and FX fees are excluded.

| Option | $29 sale, US card: fee / net | $29 sale, non-US card | $49, US card | $99, US card |
|---|---|---|---|---|
| Stripe direct + Stripe Tax Basic (not MoR) | $1.29 (4.4%) / $27.71 | $1.72 (5.9%) | $1.97 (4.0%) | $3.67 (3.7%) |
| Paddle | $1.95 (6.7%) / $27.05 | $1.95 (6.7%) | $2.95 (6.0%) | $5.45 (5.5%) |
| Polar Starter | $1.95 (6.7%) / $27.05 | $2.38 (8.2%) | $2.95 (6.0%) | $5.45 (5.5%) |
| Lemon Squeezy | $1.95 (6.7%) / $27.05 | $2.38 (8.2%) | $2.95 (6.0%) | $5.45 (5.5%) |
| Stripe Managed Payments | $2.16 (7.4%) / $26.84 | $2.59 (8.9%), plus 1% if FX applies | $3.44 (7.0%) | $6.64 (6.7%) |
| FastSpring (secondhand rate) | $2.66 (9.2%) | $2.66 | $3.84 (7.8%) | $6.79 (6.9%) |
| Gumroad (direct link) | $3.40 (11.7%) / $25.60 | $3.40 | $5.40 (11.0%) | $10.40 (10.5%) |
| Mac App Store (SBP) | $4.35 (15%) / $24.65 | $4.35 | $7.35 | $14.85 |

Stripe direct is cheapest only because you take on tax compliance yourself. That means registering and remitting wherever you have obligations, for example EU VAT on digital sales to consumers. Stripe Tax's 0.5% only calculates and collects where you are registered **[checked: stripe.com/pricing wording]**. The EU VAT detail is general knowledge that I did not re-verify today.

### 1.3 Provider notes

**Paddle**
- The pricing page says "5% + 50¢" and "Start selling globally with Paddle as your Merchant of Record." **[checked]**
- Domain approval is "mostly automatic". If it goes to manual review, it is "typically completed within an estimated 5-7 business days". **[checked]** <https://www.paddle.com/help/start/account-verification/what-is-domain-approval>
- Your site needs a product description, pricing, Terms, Refund Policy and Privacy Policy, and must be served over HTTPS. **[checked]**
- License keys: "In Paddle Classic, Paddle handles sending license keys and digital downloads... In Paddle Billing, you'll need to build this yourself." **[checked]**
- Payouts are monthly: "Paddle will send your payment by the 15th." The minimum is $100. **[checked]**

**Polar**
- Plan prices are listed in the table. The legacy "Early Member" rate is 4% + 40¢, plus 0.5% on subscriptions, and only applies to organizations created before 2026-05-27. **[checked]**
- Example from Polar's refund docs: "an order of $30 costs ~$1.60 in fees… the ~$1.60 fee stays deducted." **[checked]**
- Polar may refund up to 60 days after purchase to prevent disputes. **[checked]** <https://polar.sh/docs/merchant-of-record/fees>
- Identity verification uses Stripe Identity. The initial review happens "Before your first payout" and "can take up to 14 days." **[checked]**

**Lemon Squeezy**
- The pricing page headline reads "2026 Update: Lemon Squeezy + Stripe Managed Payments". Signup is still open ("Get started", free, no card) as of 2026-10-15. **[checked]**
- CEO post, 2026-01-28: "We're building the future of merchant of record." Lemon Squeezy is "building Stripe Managed Payments", and "Our goal is to provide Lemon Squeezy users an easy way to migrate to Stripe Managed Payments." **[checked]** <https://www.lemonsqueezy.com/blog/2026-update>
- No shutdown date has been announced. **[secondhand]**
- Fee details are in the table. **[checked]**

**Stripe Managed Payments**
- General availability: "Managed Payments is now generally available to businesses in 39 countries" (changelog, 2026-04-22). **[checked]**
- One-time payments have been supported since 2025-09-22. **[checked]**
- Software tax codes such as `txcd_10202000` (Downloadable Software, personal) and `txcd_10202003` (business) are eligible. **[checked]** <https://docs.stripe.com/payments/managed-payments/eligibility>
- Access depends on an "eligibility review". Supported business locations include US, CA, GB and most EU countries, plus CH, NO, AU, HK, JP and SG. **[checked]**
- Works with Checkout and Payment Links only. Connect and Elements are not supported. **[checked]**
- Stripe "can issue refunds within 60 days of purchase". **[checked]**
- Stripe Sessions recap (2026-04-29): "All digital businesses can now use Managed Payments." **[checked]** <https://stripe.com/blog/everything-we-announced-at-sessions-2026>

**Gumroad**
- "10% + $0.50" per transaction, and "30%" for Discover marketplace sales. **[checked]**
- "Since January 1, 2025, Gumroad handles ALL your tax obligations." **[checked]**

**DevMate-style frameworks**
- DevMate, now part of MacPaw: "Starting September 1, 2025, we will close DevMate for external developers." New licenses, the activation API and update delivery all stop. **[checked]** <https://announcement.devmate.com/>
- An earlier end-of-life notice was published in 2019. **[secondhand]** <https://mjtsai.com/blog/2019/08/27/devmate-end-of-life>

**Keygen.sh**
- Free Dev tier: "up to 100 active licensed users (ALUs) and 10 product releases". Dev and trial accounts get hard limits (HTTP 402). **[checked]**
- Paid tier prices did not render on the page (it shows "Loading plans…"). Secondhand figures conflict: $24/mo Weekender and $49/mo Startup, versus $49/$79/$129 tiers. **[secondhand]**
- A self-hosted Keygen CE is free, and Keygen describes itself as "Fair Source". **[checked]** <https://keygen.sh/pricing/>

**Sparkle**
- Version 2.10.0 was released 13 Sep. The page shows no year, but the notes include a fix "for delta updates on macOS 27", which means 2026.
- 2.10.0 requires macOS 12.0+ and drops CocoaPods. **[checked]**

**Developer ID housekeeping for direct download**
- "The original Developer ID Certification Authority (Sub-CA) expires on February 1, 2027."
- `.pkg` installers signed with affected certificates "will no longer install" after that date.
- Notarized apps that carry a secure timestamp keep working.
- New certificates come from the G2 Sub-CA. **[checked]** <https://developer.apple.com/news/?id=w4atic4c>

**Rosetta**
- "macOS 27: Final release to support Rosetta." Ship universal or Apple silicon builds. **[checked]** <https://developer.apple.com/news/?id=w5ngl9k2>

### 1.4 Mac App Store: the US court case and Apple's 5% proposal

- **Small Business Program:** 15% commission for developers with ≤ $1M proceeds in the prior calendar year. **[checked]** <https://developer.apple.com/app-store/small-business-program/>
- **US link-outs are allowed.** The App Review Guidelines (last updated 2026-06-08) say link entitlements "are not required for developers to include buttons, external links, or other calls to action in their United States storefront apps". **[checked]** <https://developer.apple.com/app-store/review/guidelines/>
- **The current commission on US link-out purchases is 0%.** Apple has collected nothing since the April 30, 2025 contempt order. **[secondhand]** MacRumors 2026-08-13 <https://www.macrumors.com/2026/08/13/app-store-fees-apple-link-outs/>; AppleInsider 2026-08-13
- **Apple's proposal, filed 2026-08-13.** In its remand proffer (Case 4:20-cv-05640-YGR, Dkt. 1708), Apple asked the court to approve "15% for standard apps… 10% for the Video Partner Program, the News Partner Program, the Mini Apps Partner Program, and subscription renewals; and 5% for Small Business Program apps." **[checked-mirror: court PDF hosted by 9to5Mac]** <https://9to5mac.com/wp-content/uploads/sites/6/2026/08/Epic_Games_Inc_v_Apple_Inc__candce-20-05640__1708.0.pdf>
- **Status of the 5% proposal.** It is a proposal only. I found no district-court ruling setting a rate as of 2026-10-15. **[secondhand + my search]** MacObserver (2026-09-12) says no rate is set. People of Internet (2026-10-01) says Epic has about 60 days to respond, followed by briefing and a hearing.
- **Supreme Court**, case No. 25-1311 **[checked]** <https://www.supremecourt.gov/docket/docketfiles/html/public/25-1311.html>:
  - Cert was granted 2026-06-30, "limited to Question 1" (contempt).
  - Apple's application to stay the district court was denied by Justice Kagan on 2026-08-13.
  - Apple's merits brief was filed 2026-09-14. Epic's brief is due 2026-11-13.
  - No argument date has been set.
- **Relevance to you [analysis]:** this only matters if you ship on the Mac App Store and link out from the US storefront. A direct-download app pays none of this.

### 1.5 Refundable pre-orders and deposits

| Mechanism | Who supports it | Caveats |
|---|---|---|
| Card stored now, charged on release | **Gumroad** native pre-orders **[checked existence; mechanics secondhand]**. **Mac App Store** pre-orders, 2–180 days ahead **[checked]**. Apple's page does not state when the buyer is charged | You need a firm release date |
| Save the card (no charge) and charge later off-session | **Stripe direct:** Checkout `mode=setup` **[checked]** <https://docs.stripe.com/payments/checkout/save-and-reuse>. **Stripe Managed Payments:** only `setup_future_usage` *during a payment* (since 2026-09-03) **[checked]** | With Stripe direct you handle tax at charge time. Later charges may need 3-D Secure re-authentication **[secondhand]** |
| Authorize now, capture later | **Stripe direct:** a 7-day hold on most card networks (Visa merchant-initiated holds last 4 days 18 h). Holds up to 30 days need IC+ pricing; Visa adds 0.08% for other merchant categories **[checked]** | Too short for a long pre-order |
| Charge now, promise a refund | All of them | MoR and Stripe fees are **not returned** on refunds (Polar, Lemon Squeezy and Stripe confirmed **[checked]**; Paddle not checked). Polar, Lemon Squeezy and Stripe Managed Payments can also issue refunds themselves within 60 days **[checked]** |

**[analysis]** For a dev tool, the cleanest option is usually to skip pre-orders and sell an "early access" license now. Deliver a working beta key immediately and offer a refund window. Card networks treat this better than charging for something not yet delivered, and every MoR supports it.

### 1.6 License keys for a Mac app: options

1. **Polar license keys.** The app calls `POST https://api.polar.sh/v1/customer-portal/license-keys/activate` once and `/validate` on each launch, passing `key`, `organization_id` and an optional `activation_id`. No secret is shipped in the app. **[checked]**
2. **Lemon Squeezy License API.** Activate, validate and deactivate endpoints; the docs example shows no API key; rate limit 60 requests/min. **[checked]** The platform's future is uncertain (see §1.3).
3. **Gumroad license verify API.** Requires `product_id` for products created after 2023-01-09. Supports multi-seat licenses and exposes refund and dispute flags. **[checked]**
4. **Paddle Billing or Stripe plus Keygen (or your own server).** A `transaction.completed` webhook creates the license. Keygen's free tier covers 100 active licensed users. **[checked]**
5. **Sparkle plus a simple offline key.** For example, an Ed25519 signature over email and product, verified with a public key embedded in the app. Zero infrastructure, but no revocation. **[analysis]** CocoaFob is an older open-source option for this; I did not check it (GitHub API was blocked).

**[analysis]** Use the MoR's key system (Polar) and cache the last good validation for offline grace, for example 14 days. Ship with a Developer ID signature, notarize, and use Sparkle for updates.

### 1.7 Recommendation (solo dev, first sale within days) [analysis built on the checked facts above]

1. **Day 0–1: Polar, Starter plan.**
   - Create a product with a License Key benefit and a checkout link on your site.
   - Fees: 5% + 50¢, plus 1.5% on non-US cards. No monthly fee.
   - You can take orders while the payout review runs; it can take up to 14 days and only gates payouts.
   - Have a live site with pricing, Terms, Privacy and Refund pages. Both Polar and Paddle reviews look for these, and r/MacApps Tier 2 also requires Terms and Privacy pages (see §5.3).
2. **Same-day fallback: Gumroad.**
   - About 11.7% total on a $29 sale. You get MoR, license keys and native pre-orders with no integration work.
   - Move to Polar or Paddle once sales justify the effort.
3. **Use Paddle instead of Polar if** you need invoicing, B2B, or enterprise procurement, which favor Paddle's long track record. Paddle does not issue license keys in Billing, so add Keygen.
4. **At meaningful volume: Stripe Managed Payments.**
   - Total on a US card is 6.4% + 30¢. Its value is the Stripe ecosystem, not a lower fee.
   - Pair it with Keygen for licenses.
5. **Mac App Store as a second channel only if the app works sandboxed.**
   - The 15% SBP fee is offset by discovery, App Store featuring nominations, and r/MacApps Tier-1 trust (§5).
   - It is required if you want the free Private Cloud Compute model (§2.4).

---

## 2. Apple Foundation Models on macOS 27 (WWDC26)

macOS 27 "Golden Gate" shipped 2026-09-14 for Macs with an M1 or newer. 27.0.1 shipped 2026-09-28 and 27.2 betas are under way. **[secondhand]** <https://9to5mac.com/2026/09/09/apple-confirms-macos-27-golden-gate-launch-date-september-14/>, <https://www.macrumors.com/2026/09/28/apple-releases-macos-27-0-1/>

### 2.1 On-device model: context window and the runtime API

- **API:** `SystemLanguageModel.contextSize` is "The maximum context size in tokens that the model supports." Its declaration is `@backDeployed(before: iOS 26.4, macOS 26.4, visionOS 26.4) final var contextSize: Int { get }`. Token counting uses `tokenCount(for:)`. **[checked: Apple doc JSON]** <https://developer.apple.com/documentation/foundationmodels/systemlanguagemodel/contextsize>
  - WWDC26 session 241: "In iOS 26.4, we released new APIs for inspecting the model's context size and counting the tokens in instructions, prompts, and transcripts." **[checked]**
- **The size itself: Apple's sources conflict. Read it at runtime and do not hard-code it.**
  - TN3193 (updated 2026-03-31): "context window of 4096 tokens per LanguageModelSession". **[checked]** <https://developer.apple.com/documentation/technotes/tn3193-managing-the-on-device-foundation-model-s-context-window>
  - The macOS 27 PCC article's comparison table: on-device "4K" vs PCC "32K". **[checked]** <https://developer.apple.com/documentation/foundationmodels/adding-server-side-intelligence-with-private-cloud-compute>
  - Session 319 transcript: "The on-device model offers 4k, and with PCC you get 32K." **[checked]** <https://developer.apple.com/videos/play/wwdc2026/319/>
  - Session 241 code sample: `let model = SystemLanguageModel(); print(model.contextSize) // 8192`. **[checked]** <https://developer.apple.com/videos/play/wwdc2026/241/>
- **New in macOS 27: two on-device variants.** `SystemLanguageModel.variant` returns `.core3` ("AFM 3 Core") or `.coreAdvanced3` ("AFM 3 Core Advanced"). **[checked]**
  - **[analysis]** The 4K vs 8K conflict may track the variant or the hardware tier. One report says the strongest on-device model needs an M3 or later with ≥ 12 GB of RAM **[secondhand: Gadget Hacks]**. This is unverified.
- **Model versions:** the docs say there are 3 model versions so far: 26.0–26.3, 26.4, and 27.0. **[checked]**

### 2.2 Inputs and capabilities

- **Images (new on-device in 27):** "Image attachments can be created from… UIImage, NSImage, CGImage Core Image types, CoreVideo Pixel Buffers, and file URLs." Any size is accepted, but "larger images will consume more tokens." **[checked: session 241]**
  - The docs also list `Attachment`, `CGImage`, `CIImage`, `CVPixelBuffer` and image URLs. **[checked]** <https://developer.apple.com/documentation/foundationmodels/analyzing-images-with-multimodal-prompting>
- **Tool calling and guided generation (`@Generable`):** both still supported, and "Getting structured output with Generable, or calling Tools, works just the same with the PCC model." **[checked: session 319]**
- **New APIs in 27 [checked: session 241, macOS what's-new page <https://developer.apple.com/macos/whats-new/>]:**
  - `LanguageModel` protocol and `LanguageModelExecutor`
  - Dynamic Profiles
  - System tools: `BarcodeReaderTool`, `OCRTool`, and a Spotlight-backed local RAG tool
  - Evaluations framework
  - A `usage` property for token counts
  - Prompt and tool inspection in Instruments
- The Foundation Models core framework "will also be open source", including for Linux servers. **[checked: session 241 transcript]**

### 2.3 The `fm` command-line tool (macOS 27)

- **Official facts, session 334 [checked]** <https://developer.apple.com/videos/play/wwdc2026/334/>:
  - "comes pre-installed with macOS 27". The default model is on-device ("that's always available").
  - Subcommands shown: `respond`, `chat` (with `/model` and `/save`), and `schema object`.
  - Flags shown: `--model pcc`, `--image`, `--schema`, `--instructions`, `--help`.
  - Example: `fm respond "…" --image Screenshot.png --model pcc --schema schema.json` returns JSON.
- **Full man page [checked-mirror]** <https://keith.github.io/xcode-man-pages/fm.1.html>:
  - Commands: `respond`, `chat`, `count-tokens`, `schema`, `serve` (a Chat Completions server), `models`, `quota-usage`, `config`, `license`.
  - Global flags: `-m/--model system|pcc|<provider model>`, `--model-provider <name|base URL>`, `--model-provider-header`.
  - `respond` flags: `-i/--instructions`, `--schema`, `--text`, `--image`, `--resume`, `--save-transcript`, `--[no-]stream`, `-g/--greedy`, `-v`, `--use-case general|content-tagging`, `--guardrails default|permissive-content-transformations`.
  - `serve` flags: `--host`, `--port`, `--socket`.
  - Files: `~/.fm/sessions/`, `~/.fm/config.json`.
  - The terms must be accepted machine-wide with `sudo fm license`. Without that, `fm` exits with status 69.
- **Can any app or script call it? [secondhand]**
  - **Scripts:** yes for the on-device model. It reads stdin, writes stdout, and is preinstalled at `/usr/bin/fm`. <https://mac.install.guide/terminal/fm-command>, <https://modelfit.io/blog/macos-27-fm-cli-local-model-terminal/>
  - **Private Cloud Compute from scripts:** blocked by a TTY / parent-process gate ("Error: PCC inference is not available in this context"). It works from an interactive terminal, or via `fm serve` started from a terminal (Pete Goldsmith, 2026-07-02, beta) <https://petegoldsmith.com/2026/07/02/2026-07-02-fm-pcc-not-available-in-this-context/>.
  - Two hands-on reports on 27.0 say `--model pcc` is rejected outright. **Treat PCC through `fm` as unreliable.**
  - **`fm serve`:** listens on loopback, `127.0.0.1:1976` by default. Endpoints: `POST /v1/chat/completions`, `GET /v1/models`, `GET /health`. Tool definitions are ignored or rejected. **[secondhand]**
  - **Sandboxed Mac App Store apps:** whether they can spawn `fm` is not documented. **[analysis]** In an app, use the Swift framework rather than shelling out.

### 2.4 Python SDK

- **Install:** `pip install apple-fm-sdk`, then `import apple_fm_sdk as fm`.
- **License:** Apache-2.0.
- **Requirements:**
  - README: macOS 26.0+, Python 3.10+, Xcode 26.0+, and Apple Intelligence turned on.
  - Session 334: Python ≥ 3.10, Xcode installed, an Apple silicon Mac.
- **Features:**
  - README: text, streaming, guided generation.
  - Session 334 adds image inputs and tool calling.
- **Sources [checked]:** <https://github.com/apple/python-apple-fm-sdk>, <https://apple.github.io/python-apple-fm-sdk/>
- **No Private Cloud Compute:** a project contributor wrote "we do not currently plan to add support for Private Cloud Compute in this Python SDK" and pointed to `fm serve` (2026-06-19, issue #13). **[checked]** <https://github.com/apple/python-apple-fm-sdk/issues/13>

### 2.5 Private Cloud Compute (PCC) model: conditions for third parties

- **Class and capabilities:** `PrivateCloudComputeLanguageModel` (iOS/macOS/visionOS/watchOS 27).
  - "32K-token context size and stronger reasoning". `contextSize // 32768` in session 319.
  - Reasoning levels: `.light`, `.moderate`, `.deep`. **[checked]**
- **Eligibility [checked]** <https://developer.apple.com/private-cloud-compute/>:
  - "Are enrolled in the App Store Small Business Program."
  - "Have fewer than 2 million first-time app downloads from any of their apps on the App Store."
  - Have the managed entitlement `com.apple.developer.private-cloud-compute` assigned through a capability request.
  - "eligible developers can use PCC in their apps **distributed on the App Store**, and test PCC features via TestFlight or ad hoc distribution."
  - If you exceed the threshold or leave the SBP, you "must migrate… within 6 months."
- **Cost and limits:** "no cloud API cost". Each user has a daily limit counted against their iCloud account; iCloud+ raises it. Apple adds: "Expanded access to such features will be available for a fee in the future." **[checked]**
  - APIs for the limit: `quotaUsage`, `quotaLimitReached` error, `limitIncreaseSuggestion.show()`. **[checked]**
- **[analysis]** A Developer ID (direct-download) app does not appear eligible for PCC. If PCC matters, you need a Mac App Store build.

### 2.6 Claude, Gemini and MLX through Foundation Models sessions

- **Mechanism:** any model that conforms to `LanguageModel` plugs into `LanguageModelSession(model:)`. Third-party models are "typically billed per-token". **[checked: sessions 241 and 339]** <https://developer.apple.com/videos/play/wwdc2026/339/>
- **Claude** — Anthropic's `ClaudeForFoundationModels`, status "Beta" **[checked]** <https://github.com/anthropics/ClaudeForFoundationModels>, <https://claude.com/blog/claude-for-foundation-models>:
  - Install: `.package(url: "https://github.com/anthropics/ClaudeForFoundationModels.git", from: "0.1.0")`, Apache-2.0.
  - Auth options: `.appAttest(clientID:)` (recommended; "usage bills to your workspace", no key in the app), `.apiKey` (for the simulator; "don't release with one"), or `.proxied`.
  - Server tools: web search, web fetch, code execution.
  - Blog announcement dated 2026-06-08.
- **Gemini** — via Firebase AI Logic, "in preview" (2026-06-09). Requests can be attested with Firebase App Check. **[checked]** <https://firebase.blog/posts/2026/06/apple-foundation-models-gemini>
- **MLX and Core AI** — `MLXLanguageModel(modelID: "mlx-community/…")` from `MLXFoundationModels`, and `CoreAILanguageModel(resourcesAt:)`, both open-sourced. **[checked: sessions 339 and 241]**

---

## 3. macOS 27 / Xcode 27 overlap with indie tools

"Threatened tools" and threat levels are **[analysis]**. Feature facts carry their own flags.

| Change | Version | Facts (flag) | Indie tools affected / threat |
|---|---|---|---|
| **Coding agents in Xcode** | 26.3 introduced; 27 expands | Plan mode (`/plan`), sub-agents, transcript in the editor, Apple Document Search, build/preview/test tools, image attachments, inline annotations **[checked: sessions 258, 259]**. "we worked with Anthropic, OpenAI, Google to bring their agents right into Xcode". Any agent, including local ones, via the Agent Client Protocol (ACP) **[checked: session 382]**. Claude Sonnet & Opus and ChatGPT sign-in; any Chat Completions provider, including local ones, via `/v1/models` and `/v1/chat/completions` **[checked]** <https://developer.apple.com/documentation/xcode/setting-up-coding-intelligence> | **High for:** Cursor/Windsurf/VS Code + SweetPad used for Swift; Copilot for Xcode; Xcode sidebar assistants (Alex-style); paid context tools like Repo Prompt (now free/OSS, §4.2) |
| **Xcode plugins: skills + MCP tools + agents** | 27 | Plugins use "a format created by Anthropic". They contain skills (markdown), MCP tools, and agents via ACP. "Paste a GitHub URL." Figma and GitHub shipped plugins. Per-plugin permissions. A new setting lets the kernel ask Xcode before agent sub-processes touch files **[checked: session 382]**. Config folders: `~/Library/Developer/Xcode/CodingAssistant/{ClaudeAgentConfig,codex,gemini}` **[checked]** | **High for** paid Xcode-MCP wrappers. **Opportunity:** ship *your* tool as an Xcode plugin or MCP server |
| **Xcode as an MCP server for external agents** | 26.3+ | "Allow external agents to use Xcode tools". Setup: `claude mcp add --transport stdio xcode -- xcrun mcpbridge` and `codex mcp add xcode -- xcrun mcpbridge` **[checked]** <https://developer.apple.com/documentation/xcode/giving-external-agents-access-to-xcode> | **High for** XcodeBuildMCP-type build/test bridges |
| Localization agents and "Generate Translations" in String Catalogs | 27 | **[checked: session 258]** | String Catalog translators (e.g., TranslateKit-style apps) |
| Device Hub (simulators and devices in one window; accessibility inspector) | 27 | **[checked: session 258]** | RocketSim, Control Room (medium) |
| `fm` CLI + `fm serve` (OpenAI-compatible) + Python SDK | macOS 27 | §2 | Small "Apple Intelligence CLI/server" wrappers (high). Ollama/LM Studio only for tiny tasks (low: 4K context, no tools over HTTP) |
| Foundation Models `LanguageModel` protocol with Claude/Gemini/MLX packages | 27 | §2.6 | Swift multi-LLM SDKs and wrappers (e.g., Hugging Face AnyLanguageModel, SwiftOpenAI-style packages) (medium–high) |
| **Containers:** `container` 1.0 and "container machines" | Shipped on GitHub 2026-06-09; 1.5.0 on 29 Sep | Persistent Linux environments in "own, lightweight virtual machine", OCI images, mirrors your username and working directory. Separate download from GitHub; a `container k8s` plugin arrived in 1.2.1 **[checked]** <https://developer.apple.com/videos/play/wwdc2026/389/>, <https://github.com/apple/container/releases> | OrbStack, Docker Desktop, Colima, Podman/Rancher Desktop (medium, rising) |
| Spotlight clipboard history | Tahoe 26, kept in 27 | ⌘-Space then ⌘4; "Clear History" **[checked]** <https://support.apple.com/guide/mac-help/search-your-clipboard-history-mchl40d5b86b/mac>. Off by default, plain text only, 30 min / 8 h / 7 days retention **[secondhand: Paste blog]** | Paste, Maccy, Clipy, PastePal, ClipBook (low–medium: basic needs only) |
| Spotlight actions and quick keys (26); "Ask Siri" as top hit (27); faster shortcuts/actions indexing (27) | 26/27 | 26: "hundreds of actions directly from Spotlight", "quick keys" **[checked]** <https://www.apple.com/newsroom/2025/06/macos-tahoe-26-makes-the-mac-more-capable-productive-and-intelligent-than-ever/>. 27: Siri AI "Search or Ask" in Spotlight **[secondhand: MacRumors quoting Apple]** | Raycast, Alfred, LaunchBar (medium) |
| Menu bar customization (26); updated menu bar icons and Ethernet status (27) | 26/27 | "more ways to customize what controls appear in the menu bar" **[checked]**. 27 items **[secondhand: MacRumors list of 250 changes]** | Bartender, Ice, Hidden Bar (medium). iStat Menus/Stats (low) |
| Window management | 27 | Only "more consistent window positioning persistence across external displays" and "more distinct active windows" **[secondhand]**. Built-in tiling dates from macOS 15 (not re-checked) | Rectangle, Magnet, Moom: nothing new beyond 2024 |
| Visual Intelligence on Mac; Shortcuts screenshot/notification/keyboard automations, "Use Model", persistent storage | 27 | Visual Intelligence lets you select a screen region and ask Siri **[checked: Apple App Store story]** <https://apps.apple.com/us/mac/story/id1896606928>. Shortcuts automations, Use Model and Storage **[checked: session 310]** | OCR apps (TextSniper), AI screen assistants (medium). Keyboard Maestro/BetterTouchTool (low) |
| Screenshot or screen *recording* tools | — | No first-party change found **[checked by absence: session list, macOS what's-new page, Xcode what's-new page]** | CleanShot X, Screen Studio: not threatened |
| Local dev servers / HTTPS, database GUIs, API clients, network debugging | — | No first-party change found (same scope) | TablePlus, Proxyman, Postman/Bruno, Herd/ServBay: not threatened |
| App Intents / App Schemas for Siri AI | 27 | Entity schemas feed the Spotlight semantic index; intent schemas; View Annotations API; AppIntentsTesting **[checked]**. Siri AI arrives "in beta later this year… English to start" **[checked: Apple App Store story]** | Opportunity: expose your tool's actions to Siri, Spotlight and Shortcuts |
| **Full Disk Access tightening** | announced 2026-10-02 | "we will introduce additional controls… only… with very explicit user action… As AI agents become increasingly capable" **[checked]** <https://developer.apple.com/news/?id=p6zjojqw> | Risk for any dev tool or agent that depends on FDA (onboarding friction) |

---

## 4. Revenue comparables

### 4.1 TrustMRR: verified revenue (payment-provider API keys)

**About TrustMRR [checked]**

- It verifies revenue through "a direct connection to its actual payment provider" (Stripe, Lemon Squeezy, Polar, Paddle, RevenueCat, Dodo, Creem, App Store, etc.). <https://trustmrr.com/llms.txt>
- It claims "over 15,000 startups listed".
- The Developer Tools category shows "1,543 startups with verified revenue". <https://trustmrr.com/category/developer-tools>
- All rows below were read on each startup page on 2026-10-15; each page showed "Last updated: Oct 15, 2026" or Oct 14. **[checked]**
- Age is computed from the founded month to Oct 2026. **[computed]**
- "MoR/provider" is the verification source shown on the page.
- Caveat: listings are self-selected and skew small.

**Mac apps and Mac or desktop utilities**

| Product (TrustMRR URL) | What | All-time revenue | Last 30 days | MRR | Pricing model | Founded (age) | Verified via |
|---|---|---|---|---|---|---|---|
| Voicy (/startup/voicy) | Speech-to-text app for Mac, Windows and browser extension | $188,241 | $17,754 | $12,230 | Free trial; Pro $8.49/mo; Lifetime $260; Team $6.79/user/mo | Nov 2025 (11 mo) | Stripe |
| Compresto (/startup/compresto) | macOS image/video/PDF compressor | $62,260 | $1,873 | $198 | not shown | Dec 2023 (2 yr 10 mo) | Polar |
| SlapMac (/startup/slapmac) | Novelty Mac app | $57,456 | $2,022 | – | $9.99 one-time | Mar 2026 (7 mo) | Polar |
| ExtraDock (/startup/extradock) | macOS multi-dock app | $38,830 | $2,805 | – | 1-yr $14.99; lifetime $37.20 per device; "Forever" $116.50 | Nov 2025 (11 mo) | Stripe |
| ScreenSnap Pro (/startup/screensnap-pro) | Screenshot and screen recording, Mac and Windows | $14,306 | $4,653 | – | $39 one-time | Aug 2025 (14 mo) | not captured |
| ExtraBar (/startup/extrabar) | Custom macOS menu bar | $13,965 | $878 | – | One-time $28.99 (1 Mac) / $57.99 (2) / $86.99 (3) | Dec 2025 (10 mo) | Stripe |
| Headroom (/startup/headroom) | Menu bar app that trims Claude Code/Codex inputs | $11,107 | $3,056 | $1,827 | Subscription: $3–$40/mo tiers | Mar 2026 (7 mo) | Polar |
| 1DevTool (/startup/1devtool) | Desktop "vibe coding IDE" for multiple AI CLIs (Electron) | $8,460 | $1,242 | $2 | Free; Pro $29 one-time per device | Nov 2025 (11 mo) | Lemon Squeezy |
| SuperShrimp (/startup/supershrimp) | macOS posture app | $7,457 | $170 | – | $29 one-time (discounted to $17) | Feb 2026 (8 mo) | Stripe |
| TypeBoost (/startup/typeboost) | macOS system-wide AI text prompts | $7,224 | $16 | $16 | Free; Pro $5/mo | Mar 2025 (19 mo) | Stripe |
| autozoom (/startup/autozoom-cross-platform) | Auto-zoom screen recorder (Tauri) | $3,167 | $394 | $154 | $7.99/mo or $69 lifetime | Feb 2026 (8 mo) | Dodo Payments |
| Orchard (/startup/orchard) | Menu bar MCP bridge from AI agents to Apple apps | $2,270 | $650 | $50 | Free; $2.99/mo or $24.99/yr; lifetime $39.99 | Jul 2025 (15 mo) | Stripe |
| terrific.tools (/startup/terrific-tools-desktop) | Offline file converter, Mac and Windows | $2,270 | $113 | – | $25 one-time | Nov 2024 (23 mo) | Creem |
| Scribbble (/startup/scribbble) | Screen annotation for Mac | $1,986 | $574 | – | Free to try; one-time license | Sep 2025 (13 mo) | Lemon Squeezy |
| CtrlOps (/startup/ctrlops) | Desktop app to manage Linux servers (Tauri) | $1,777 | $1,120 | $21 | $7/mo, $70/yr, $149 lifetime | Apr 2026 (6 mo) | Creem |
| MAC+ (/startup/mac) | Animated wallpapers and widgets for macOS | $1,771 | $230 | $36 | Free; €1.99/mo; €9.99 lifetime | Jun 2026 (4 mo) | Polar |
| Clamshell (/startup/clamshell) | Menu bar app: keep MacBook running lid-closed for agents | $528 | $289 | – | $9.99 lifetime ($19.99 for 3 Macs); also on Setapp | May 2026 (5 mo) | Lemon Squeezy |
| Build Mac App (/startup/build-mac-app) | Mac app boilerplate (licensing, notarization, updates, payments) | $161 | $161 | – | $49 one-time | Sep 2026 (1 mo) | Creem |

**Developer tools (web/API) for context**

| Product | What | All-time | Last 30 days | MRR | Pricing | Founded (age) | Verified via |
|---|---|---|---|---|---|---|---|
| ShipFast (/startup/shipfast) | Next.js SaaS boilerplate | $1,272,045 | $1,146 | – | $199 / $249 / $299 bundle, one-time | Jul 2023 (3 yr 3 mo) | Stripe |
| LLM Gateway (/startup/llm-gateway) | Open-source LLM API gateway | $1,000,116 | $259,539 | $78,764 | Free tier + usage | May 2025 (17 mo) | not captured |
| CodeFast (/startup/codefast) | Coding course | $833,600 | $5,031 | – | $169; $299 with ShipFast | Aug 2024 (26 mo) | Stripe |
| Capgo (/startup/capgo) | Capacitor live updates | $561,593 | $34,989 | $32,596 | Subscription; 14-day trial | Nov 2021 (4 yr 11 mo) | Stripe |
| Apiframe (/startup/apiframe) | One API for many AI models | $495,282 | $48,296 | $37,365 | Credits; from $39/mo | Aug 2021 (5 yr 2 mo) | Stripe |
| Web3Forms (/startup/web3forms) | Form backend API | $325,008 | $44,734 | $42,249 | Freemium subscription | Dec 2020 (5 yr 10 mo) | Paddle |
| Screenshot to Code (/startup/screenshot-to-code-whimsyworks-inc) | AI screenshot to code | $259,963 | $4,537 | $4,758 | Subscription | Nov 2023 (2 yr 11 mo) | Stripe |

**What the TrustMRR data says [computed / analysis]**

- Among self-listed Mac utilities, the top earners have a strong consumer hook. Voicy (dictation) leads at about $18k/month. Most others earn $100–$5k/month.
- One-time pricing between $5 and $40 dominates. Several sellers verify through Polar, Lemon Squeezy, Creem or Dodo, all MoRs.
- New Mac apps launched in 2026 commonly show lifetime revenue under $10k.

### 4.2 Public revenue disclosures for named products (2024–2026)

| Product | What I found | Flag / source |
|---|---|---|
| **Tailwind Plus (Tailwind Labs)** | Adam Wathan, 2026-01-07: "our revenue is down close to 80%". "Traffic to our docs is down about 40% from early 2023". "75% of the people on our engineering team lost their jobs." | **[checked]** <https://github.com/tailwindlabs/tailwindcss.com/pull/2388#issuecomment-3717222957> |
| **shadcn kits: Shadcnblocks** | "$1M ARR", described as "Profitable, bootstrapped". 6,345 paid users ("All Access and lifetime"), 33,234 free users, started Jan 2024. These are self-reported company figures. Acquired Kibo UI on 2025-10-28 | **[checked]** <https://www.shadcnblocks.com/about>, <https://www.shadcnblocks.com/blog/announcing-kibo-ui-acquisition> |
| **ShipFast (boilerplate)** | $1,272,045 all-time verified, $1,146 in the last 30 days (Oct 2026). Separately, "over $100,000 per month" by end of 2024 (unverified) | **[checked]** TrustMRR. **[secondhand]** <https://levelup.gitconnected.com/how-to-get-25-000-visitors-from-hacker-news-solo-founder-marc-lous-exact-formula-17cd13ce8376> |
| **Repo Prompt** | Reached "5-figure MRR within a year". Pricing was $14.99/mo, $149/yr, and lifetime $349–399. **2026-05-27:** the founder joined OpenAI; "licensing restrictions have been fully removed and all current subscriptions have been cancelled"; the Community Edition is free under Apache-2.0 from 2026-06-13. OpenAI is giving Codex credits to Repo Prompt users | **[secondhand]** <https://startupfounderstories.com/data-insights/by-industry/developer-tools>, <https://vibecoding.app/blog/repo-prompt-review>, <https://www.producthunt.com/p/repo-prompt/repo-prompt-is-now-free-and-soon-to-be-open-source> |
| **Wispr Flow** | $280M Series B at a $2B valuation, $361M raised in total (2026-08-17). No ARR published | **[secondhand: TechCrunch]** <https://techcrunch.com/2026/08/17/wispr-raises-280m-at-2b-valuation-as-it-looks-beyond-dictation/> |
| **Raycast** | $30M Series B led by Atomico (Sept 2024). Dealroom puts revenue at $1–10M. No ARR published | **[secondhand]** <https://www.lw.com/en/news/2024/09/latham-advises-atomico-on-raycasts-us30-million-series-b>, <https://dealroom.co/companies/raycast/> |
| **Screen Studio** | About $30k in its first month (founder, Make Lemonade podcast). Current price reportedly $29/mo or $108/yr. No 2024–26 revenue disclosure found | **[secondhand]** <https://make-lemonade.simplecast.com/episodes/taking-on-adobe-with-his-bootstrapped-tool-screen-studio-adam-pietrasiak-_vH5kqBv>, <https://www.systemaic.com/teardowns/screen-studio> |
| **Proxyman** | Indie Hackers profile lists "$75K / mo", self-reported and undated. The page returned 403 to my fetch | **[secondhand]** <https://www.indiehackers.com/product/proxyman/revenue> |
| **VoiceInk** | GPL v3 source with paid one-time builds; reported tiers conflict ($25/$39/$49 vs $29/$49/$69). Site claims "200k+ Downloads" (first-party). No revenue disclosed | **[secondhand]** <https://tryvoiceink.com/>, <https://www.getvoibe.com/resources/voiceink-pricing/> |
| **MacWhisper** | About $100k revenue and 57,574 downloads via Gumroad, undated | **[secondhand]** <https://startupsemail.substack.com/p/100000-revenue-with-a-simple-mac> |
| **CleanShot X** | Only a 2019 interview ("approaching… $100k"). Nothing for 2024–26 | **[secondhand]** |
| **TablePlus, OrbStack, Superwhisper, Kaleidoscope, Tower** | No public 2024–2026 revenue disclosure found | searched; none found |

---

## 5. Launch channels for developer tools (2026)

### 5.1 Hacker News (Show HN)

- **Rules:**
  - "Show HN is for something you've made that other people can play with."
  - "Don't post landing pages or fundraisers."
  - "ideally without barriers such as signups or emails."
  - "Please don't ask friends to upvote or comment."
  - **[checked]** <https://news.ycombinator.com/showhn.html>
- **Show HN is far more crowded than it was** (my queries against the HN Algolia API, `tags=show_hn`, by `created_at_i`) **[computed]**:

  | Period | Show HN posts | Share with >10 points | Share with ≥100 points |
  |---|---|---|---|
  | 2022 H1 | 4,945 | 21.5% | 6.4% |
  | 2024 H1 | 8,210 | 16.1% | 5.1% |
  | 2025 H1 | 12,449 | 12.2% | 3.5% |
  | 2026 H1 | 25,967 | 7.1% | 1.7% |
  | 2026 Q3 | 11,654 | 8.0% | 1.5% |

- **Mac posts specifically [computed]:**
  - Show HN posts with "Mac" in the title: 245 (2024), 513 (2025), 1,377 (Jan–Sep 2026).
  - Share reaching ≥100 points: 6.1%, then 3.3%, then 2.8%. Algolia prefix matching makes these counts approximate.
  - Top 2026 posts with "macOS" in the title: boringBar (520 points), Ghost Pepper (467), Auto-identity-remove (325), Tolaria (318).
- **Example outcomes:**
  - cmux (native macOS terminal for AI agents) "hit #2 on Hacker News" on 2026-02-19 and spread after Mitchell Hashimoto shared it. **[checked]** <https://cmux.com/blog/show-hn-launch>
  - DevUtils (Mac app, 2020): front page brought "14k unique visitors… about 100 purchases in a single day". After adding the Mac App Store version, the MAS was "almost 50% of the sales". **[checked: founder's Indie Hackers post, via search extract]** <https://www.indiehackers.com/post/my-app-gets-to-the-hn-front-page-0de947a036>
  - Third-party traffic estimates: front page roughly 2.5k–25k visitors depending on rank; developer-tool conversion roughly 2–5%. **[secondhand]** <https://dodatathings.dev/blog/launch-platform-roi-the-math-nobody-shares>

### 5.2 Product Hunt

- **Product Hunt's own Q2 2026 report:**
  - Developer Tools had 633 launches, "up 136% from last year". AI had 1,111 launches (+46%).
  - Average upvotes: Developer Tools 201, all launches 190.
  - **[checked: producthunt.com post 2026-08-29, via search extract]** <https://www.producthunt.com/p/general/product-hunt-s-state-of-tech-discovery-q2-2026>
- **Featuring has collapsed:**
  - A user analysis on Product Hunt (2026-08-24): 2023 had about 41k submissions and 15k featured. 2026 so far has 147k submitted and only about 4.9k featured, roughly 1 in 30. **[secondhand]** <https://www.producthunt.com/p/general/product-hunt-is-on-track-for-228k-submissions-in-2026-5x-more-than-just-two-years-ago>
  - Another analysis says less than 3% of launches were featured in Jun–Sep 2026. **[secondhand]** <https://trudov.com/p/product-hunt-trends-8x-the-launches>
- **Solo makers are disadvantaged:** they reached a day's top 10 35.8% of the time, versus 74.2% for teams of five or more. **[secondhand]** <https://www.launchpact.io/research/product-hunt-launch-study>
- "Coming soon" pages were removed on 2025-08-28. **[secondhand]**

### 5.3 Reddit r/MacApps (self-promotion rules)

- **Source:** the moderator post "r/MacApps Mods Went Too Far! What's Changing (Phase 3)" by u/Mstormer, dated 2026-03-19. **[checked-mirror: redlib]** <https://redlib.vanillax.me/r/macapps/>. Reddit itself blocked my fetch.
- **Main feed is open to three tiers:**
  - **Tier 1 (Trust):** "Mac App Store developers… Notarization alone does not count." Or a GitHub project with "1yr+ consistent… history and… 100+ stars". Or developers with a recognized flair. All need "10+ local karma".
  - **Tier 2 (Transparency):** if you are not on the Mac App Store, the post must include "A developer portfolio with a real life identity, LinkedIn (ideal), and real contact details" and "A website that has a Privacy Policy and Terms of Service."
  - **Tier 3:** everyone else posts in "The App Pile" megathread.
- **Frequency (Rule 3):** "not permitted more than once per developer in 30 days… counted from the last app post, even if it was removed."
- **Post format (PCP):** Problem, Comparison (name one or two competitors), Pricing with amounts and a link.
- **Previous phase:** the stricter rules removed "2,700+ items", generated "1,400 modmail messages", and views dropped by 204k.
- **Megathread rules (mirror text):** dictation apps are directed to the megathread, and posts may not link directly to .zip or .dmg files. **[checked-mirror]**
- **Removal triggers:** the post warns that AI-style text (em dashes) and an unverified email trigger auto-removal.

### 5.4 Apple featuring

- "Featuring Nominations in App Store Connect". "Please give our team a minimum of two weeks notice", and "up to three months in advance" is recommended. **[checked]** <https://developer.apple.com/app-store/getting-featured/>
- **[analysis]** This applies only to App Store apps. A direct-download app has no Apple featuring path.

### 5.5 Being recommended by ChatGPT or Claude

- Vercel CEO Guillermo Rauch on X: ChatGPT referred "4.8% of new Vercel signups" (2025-03-06), then "10%" (2025-04-09), up from under 1% about six months earlier. **[secondhand via]** <https://praised.co/blog/vercel-ai-referrals-case-study>
- Tally said AI is its top acquisition channel (June 2025). **[secondhand]** <https://www.rankwit.ai/post/the-shift-has-already-begun-how-ai-is-redefining-user-acquisition>
- **[analysis]** What to do:
  - Publish `llms.txt` (TrustMRR and Vercel both do; TrustMRR's is **[checked]**).
  - Write plain comparison pages ("X vs Raycast/Alfred…").
  - Get organic Reddit and HN threads, since they are cited by AI assistants.
  - Add an MCP server or Xcode plugin so agents can actually call your tool.

### 5.6 X and TrustMRR

- Data on X as a channel is thin.
- Marc Lou shows 410.7k followers on his TrustMRR page **[checked]**.
- cmux's spread came from a high-profile share on X **[checked]**.
- TrustMRR describes itself as having "200K monthly visitors" and being "used as a source of trust across Reddit" **[checked: self-description]**. Listing verified revenue there doubles as distribution.

### 5.7 Suggested launch sequence [analysis]

1. Week 0: soft launch to your X audience with a discounted "early access" license from Polar.
2. Post on r/MacApps with Tier 2 transparency. Have Terms and Privacy pages and a real identity ready, and use the PCP format.
3. Post a Show HN with a free trial and no signup wall. Lead with a technical, first-person title, and answer every comment.
4. Add a Product Hunt launch for the backlink. Expect little else unless you are featured.
5. Add an `llms.txt`, comparison pages, and an MCP/Xcode-plugin surface so AI assistants and agents can find your tool.
6. If the app can be sandboxed, add a Mac App Store build. It gives r/MacApps Tier-1 trust, Apple featuring nominations, and PCC eligibility.
