# NVIDIA Corporation (NVDA) — Coverage File

**Data as of:** Q2 FY2027, quarter ended 26 Jul 2026 (10-Q filed 26 Aug 2026); 8-Ks through 3 Sep 2026; market data 4 Sep 2026
**File last updated:** 7 Sep 2026

---

## 0. 30-second reopen

- **Business** — Sells rack-scale AI data centre systems (GPU + CPU + networking + CUDA software) as one co-designed unit; Data Center is 92% of revenue [Q2 FY2027 10-Q].
- **Debate** — Whether a merchant designer that owns the architecture but rents the two physically scarce inputs (HBM memory, advanced packaging) can hold ~65% operating margins as custom silicon scales.
- **Thesis** — Full-stack co-design plus CUDA lock-in makes NVIDIA the default unit of AI compute; incumbency compounds through the annual cadence while cash funds an ecosystem others must match.
- **Bear** — Demand is increasingly self-financed: $279bn of non-cancellable supply commitments and $108.5bn of guarantees sit against customer orders that cancel freely.
- **Valuation** — $5.56tn market cap, 29.1x trailing / 19.1x forward earnings; trailing EPS flattered by unrealised investment marks [Market data 4 Sep 2026].
- **Watch** — Supply-commitment trajectory, gross margin as memory costs reprice, and whether the top-three customer share keeps falling.

---

## 1. Business snapshot

The saleable unit is not a chip but a rack-scale AI system in which GPUs, Grace CPUs, NVLink and InfiniBand/Ethernet networking, systems software and algorithms are "extreme co-designed" together [FY2026 10-K]. Revenue is reported in two segments — Compute & Networking ($88.3bn of Q2 FY2027 revenue, 71.0% segment operating margin) and Graphics ($7.9bn, 49.2%) — and, since Q1 FY2027, in a rebuilt market-platform taxonomy: Data Center $89.0bn (Hyperscale $48.7bn; AI Clouds, Industrial & Enterprise $40.3bn) and Edge Computing $7.2bn [Q2 FY2027 10-Q].

The company is fabless: TSMC and Samsung produce wafers, HBM comes from SK hynix, Micron and Samsung, CoWoS is used for packaging, and Hon Hai, Wistron and Fabrinet assemble and test. About 42,000 employees, 31,000 in R&D, and more than half of engineers work on software [FY2026 10-K].

Money is made on the spread between a high system ASP and a bought-in bill of materials, amplified by software given away to make the hardware indispensable. NVIDIA discloses no unit volumes, ASPs or software revenue in any filing, so growth cannot be decomposed into volume, price and content per rack from primary sources.

## 2. Core debate

Not whether AI infrastructure spending is large — the filings settle that — but **where in the stack the profit sits, and for how long**. NVIDIA owns the architecture, the interconnect and the developer platform, but not a physically constrained step: it rents HBM capacity and advanced packaging from suppliers who are themselves capacity-limited. The bull case says architecture and software are the scarce asset and the annual cadence keeps competitors a generation behind. The bear case says the scarce asset is fab and memory capacity, that customers building their own accelerators only need "good enough" for inference, and that a designer with 75% gross margins is the obvious place for both suppliers and customers to attack.

A second live question, new this year, is whether NVIDIA is now underwriting its own demand. The August 2026 SB Energy arrangement — $105bn of residual-value guarantees on 4.25GW of leases whose tenant is an OpenAI affiliate — is a different kind of commitment from anything in the prior record [8-K 2026-08-17].

## 3. Base thesis

NVIDIA's advantage is that it sells a *system*, not a part. The economically relevant comparison for a customer is not GPU versus custom ASIC but time-to-useful-tokens across an entire data centre, where NVLink scale-up, networking, and a software stack of hundreds of libraries carry as much weight as the accelerator. That bundle is hard to assemble and harder to keep current at an annual cadence, and each generation resets the comparison before an alternative has finished catching the last one. Meanwhile the installed base and developer population make CUDA the default target, so new workloads arrive already optimised for NVIDIA. Cash generation (FY2026 operating cash flow $102.7bn, capex $6.0bn) funds an R&D budget rising 62% year on year and an ecosystem of investments and commitments no competitor can match [FY2026 10-K; Q2 FY2027 10-Q]. The concentration risk is real but is *diluting*: the largest direct customer fell from 22% of FY2026 revenue to 16% in Q2 FY2027, and ACIE revenue — AI natives, enterprises, sovereigns — grew 138% year on year, faster than Hyperscale [FY2026 10-K; Q2 FY2027 10-Q].

**Assumptions this rests on:**

1. Rack-scale co-design remains the buying unit, so competition is judged at system rather than chip level.
2. Gross margin holds near 75% despite memory being the largest and fastest-rising input cost.
3. Customer diversification continues — ACIE and sovereign demand grow faster than hyperscale.
4. The commitments and guarantees expand the addressable buildout without ever being called.
5. Export controls stay roughly where they are; China contributes essentially nothing either way.

## 4. Main bear case

The asymmetry between what NVIDIA owes and what it is owed has become the central financial fact. Supply and capacity commitments went from $119bn one quarter earlier to $279bn at 26 Jul 2026, "primarily memory and manufacturing facilities" — $92bn falling due in the remainder of FY2027 alone. Add cloud service agreements ($29bn), leases not yet commenced ($25bn), equity-investment commitments ($25bn) and capex ($8bn) for $366bn of future commitments, plus a further $56bn of AI-cloud and third-party lease arrangements and $108.5bn of guarantees [Q2 FY2027 10-Q]. Against that, "most of our sales are made on a purchase order basis" and customers "can generally cancel, change, or delay product purchase commitments with little notice and without penalty" [FY2026 10-K]. NVIDIA has already demonstrated what happens when the two sides disconnect: a $4.5bn H20 charge in Q1 FY2026 and a further $0.4bn H200 charge in H1 FY2027 [Q2 FY2027 10-Q].

Layered on top: three customers were 16%, 15% and 13% of H1 FY2027 revenue; the profit pool sits partly with input suppliers who out-earn NVIDIA at the margin line; and the hyperscalers that account for over half of Data Center revenue are the same firms designing competing silicon and are named as competitors in the 10-K.

**How it breaks:** a pause in hyperscale capex, or a single large AI-native customer failing to fund itself, converts a non-cancellable supply book into inventory write-downs and a guarantee into an assumed 20-year lease — at the same moment revenue growth stops. The equity portfolio ($42.8bn marketable, $51.2bn non-marketable) marks down in the same cycle.

## 5. Business quality

Exceptional on returns, thinner on durability than the returns suggest. Capital intensity is low — $6.0bn of FY2026 capex on $215.9bn of revenue — because the capital-heavy steps sit at TSMC and the memory makers. That is also the weakness: NVIDIA's position depends on suppliers with their own pricing power and includes no physically constrained step of its own. Switching costs are software-shaped (CUDA, libraries, developer habit) rather than contractual, and remaining performance obligations beyond one year are just $3.2bn, so no backlog cushions a demand pause [Q2 FY2027 10-Q]. Growth has been organic: only Mellanox was materially revenue-additive; the December 2025 Groq licence bought technology and people with no acquired revenue, and Hugging Face (~$11.9bn, signed 2 Sep 2026) is pending [FY2026 10-K; 8-K 2026-09-03].

## 6. Key value drivers

Data Center revenue is the whole story (+117% year on year), and within it the Hyperscale/ACIE balance (+101% versus +138%). Second is gross margin: 75.0% in H1 FY2027 versus 66.6% a year earlier, on "improved mix from Blackwell Ultra" and the non-recurrence of the H20 charge. Third is operating leverage — R&D +62% against SG&A +23%, holding opex at 8.7% of revenue. Fourth, increasingly, is the balance sheet: the equity portfolio produced $23.7bn of gains in H1, and the commitment/guarantee book decides whether growth is financed or underwritten [Q2 FY2027 10-Q].

## 7. Financial profile

FY2026 (ended 25 Jan 2026): revenue $215.9bn (+65%), gross margin 71.1%, operating income $130.4bn, net income $120.1bn, operating cash flow $102.7bn, free cash flow ~$96.7bn [FY2026 10-K]. H1 FY2027: revenue $177.8bn (+96%), operating income $117.3bn, net income $118.0bn, operating cash flow $74.4bn against $4.4bn of capex.

Three things deserve attention. First, **other income is now material to reported earnings**: $24.1bn in H1 FY2027, 20.5% of net income, almost entirely unrealised equity gains — non-marketable holdings carry $9.1bn of cumulative gross unrealised gains, up from $661m a year earlier. Operating income is the cleaner series. Second, **working capital is absorbing cash**: receivables $63.1bn (≈60 days) and inventories $31.6bn, up 48% in six months. Third, **the balance sheet has changed shape**: $25bn of senior notes issued in June 2026 took total debt to $33.5bn against $99.4bn of cash and securities, while total assets rose 55% to $320.3bn, most of the increase in equity investments and receivables [Q2 FY2027 10-Q].

## 8. Valuation

> **Market data — as of 4 Sep 2026 close (external source, not from filings)**
> Share price $230.36 · Market cap $5.56tn · Enterprise value $5.54tn · P/E 29.1x trailing, 19.1x forward · EV/EBITDA 27.5x · EV/Sales 18.3x · P/FCF 43.8x · Shares outstanding 24.15bn

On trailing twelve-month figures derived from the filings — revenue ~$303bn, operating income ~$197.6bn, net income ~$192.9bn — the multiple is not demanding for the growth rate. The caution is what sits inside the "E": TTM net income includes roughly $30bn of investment gains that are mostly unrealised marks on positions in the same customers and partners driving revenue, so earnings and asset values are correlated in the wrong direction. Against operating income the trailing multiple is nearer 28x. Free cash flow lags earnings because working capital is funding the ramp. The valuation therefore embeds both continued growth *and* the absence of a commitment or guarantee being called.

## 9. Management & capital allocation

Jen-Hsun Huang has run the company since founding it in 1993 and remains its largest individual holder (roughly 800m shares across trusts and related entities, ~3% of shares outstanding) [2026 DEF 14A]. Executive pay is heavily performance-linked: 100% of the CEO's equity is PSUs, split between annual non-GAAP operating income and three-year TSR relative to the S&P 500; CEO total target pay $35.5m. FY2026 goals paid out at maximum — worth noting that the stretch revenue goal was automatically cut from $190bn to $160bn (and operating income from $120bn to $96bn) for the H20 export controls, though actual revenue of $215.9bn cleared even the original bar [2026 DEF 14A]. Senior bench is turning over: Ajay Puri retired after 21 years as EVP Worldwide Field Operations, replaced in August 2026 by Nicholas Parker from Microsoft [8-K 2026-07-02].

Capital allocation is aggressive and increasingly two-sided. Returns: $40.4bn of buybacks in FY2026 and $39.0bn in H1 FY2027, with $99.3bn of authorisation remaining; the quarterly dividend was raised from $0.01 to $0.25 in May 2026, taking H1 dividends to $6.3bn. Deployment: $42.4bn of equity purchases in H1 FY2027, $13.0bn cash for the Groq licence, and now guarantees rather than cash as a way to secure capacity [FY2026 10-K; Q2 FY2027 10-Q].

**Claims to verify over time:** that the Groq licence translates into shipping product (management flags in the 10-K that it may not); that the SB Energy guarantee structure genuinely stays contingent; and that Hugging Face remains open to rival silicon as committed in the deal announcement.

## 10. Risks ranked by damage

### 1. Commitment/guarantee asymmetry against cancellable demand
**Damage rank:** High · **Permanence:** Medium · **Fixability:** Low
**Mechanism** — NVIDIA locks in multi-year, non-cancellable supply and now guarantees third-party leases, while customers order on cancellable POs. A demand pause hits the revenue line and the obligation line at once.
**Evidence today** — $279bn supply commitments ($92bn due within FY2027), $108.5bn of guarantees, $3.2bn of RPO beyond one year; $4.5bn and $0.4bn of inventory charges already taken on H20 and H200 [Q2 FY2027 10-Q].
**What would confirm it** — inventory provisions rising as a share of revenue; supply commitments continuing to compound faster than revenue; any guarantee moving from contingent to recognised.
**Impact on value** — charges plus assumed lease obligations at the point of maximum multiple compression.

### 2. Customer in-sourcing shifts the profit pool
**Damage rank:** High · **Permanence:** High · **Fixability:** Low
**Mechanism** — The largest customers are named competitors: Alphabet, Amazon, Microsoft, Alibaba, Baidu and Huawei all design accelerated-computing silicon internally [FY2026 10-K]. Inference workloads are the natural first target.
**Evidence today** — Hyperscale still over half of Data Center revenue; NVLink Fusion launched precisely to attach custom XPUs to NVIDIA's platform, an acknowledgement of the trend.
**What would confirm it** — Hyperscale growing materially slower than ACIE for several quarters alongside gross-margin concession.
**Impact on value** — permanent reduction in both share and margin; the multiple, not just the estimate, resets.

### 3. Input suppliers capture the margin
**Damage rank:** Medium-High · **Permanence:** High · **Fixability:** Low
**Mechanism** — Memory and advanced packaging are the physically constrained steps. NVIDIA buys HBM from three suppliers and depends on CoWoS capacity; its own supply commitments are now explicitly "primarily memory."
**Evidence today** — supply commitments more than doubling in one quarter, memory-led, while gross margin has so far held at 75.0%.
**What would confirm it** — gross margin falling with no mix explanation; cost of revenue growing faster than revenue.
**Impact on value** — every point of gross margin is roughly $3bn of annualised operating income at current scale.

### 4. Export controls and China
**Damage rank:** Medium · **Permanence:** Medium · **Fixability:** Low
**Mechanism** — Licensing requirements have twice stranded China-specific products; the PRC has separately discouraged purchases and set performance-per-watt standards for domestic data centres [Q2 FY2027 10-Q].
**Evidence today** — China Hopper shipments under 1% of Data Center revenue; H200 shipments under the new licence programme carry an unpassed-through 25% import tariff.
**What would confirm it** — controls widening beyond China, which the 10-Q explicitly warns could affect Europe, Latin America and Southeast Asia.
**Impact on value** — mostly already absorbed; the tail risk is control of *non-China* markets.

### 5. Earnings quality and investment marks
**Damage rank:** Medium · **Permanence:** Low · **Fixability:** High
**Mechanism** — Reported earnings now include large unrealised gains on stakes in customers and partners; those marks fall in the same scenario that hurts revenue.
**Evidence today** — $23.7bn of equity gains in H1 FY2027; $9.1bn of cumulative unrealised gains on non-marketable holdings.
**What would confirm it** — a quarter where operating income and net income diverge in the other direction.
**Impact on value** — presentational rather than economic, but it distorts the trailing multiple.

### 6. Key-person and succession
**Damage rank:** Medium · **Permanence:** Medium · **Fixability:** Medium
**Mechanism** — Strategy, architecture cadence and customer relationships are unusually concentrated in the founder-CEO; the 10-K names succession planning as a risk.
**Evidence today** — Huang at the centre of the platform strategy since 1993; the go-to-market EVP replaced in 2026 after 21 years.
**What would confirm it** — further senior departures without internal successors.
**Impact on value** — execution and cadence risk rather than an immediate financial hit.

## 11. Metrics to monitor

| Metric | Prior | Latest | As of | Why it matters |
|---|---|---|---|---|
| Data Center revenue | $75.2bn (Q1 FY27) | $89.0bn | Q2 FY2027 | The thesis in one line |
| Hyperscale vs ACIE mix | $43.1bn / $32.2bn | $48.7bn / $40.3bn | Q2 FY2027 | Tests diversification (assumption 3) |
| Gross margin | 74.9% (Q1 FY27) | 75.0% | Q2 FY2027 | Tests memory cost pass-through (assumption 2) |
| Largest direct customer share | 22% (FY2026) | 16% | Q2 FY2027 | Concentration direction |
| Supply & capacity commitments | $119bn (Q1 FY27) | $279bn | 26 Jul 2026 | The asymmetry (risk 1) |
| Guarantees, maximum gross exposure | $3.5bn (excl. SB Energy) | $108.5bn | Aug 2026 | Off-balance-sheet demand support |
| Inventory provisions, % of revenue | 1.4% (Q1 FY27) | 1.0% | Q2 FY2027 | Early warning on over-commitment |
| Other income as % of net income | 28.1% (Q1 FY27) | 13.0% | Q2 FY2027 | Earnings quality (risk 5) |

## 12. Thesis tripwires

| Direction | Trigger |
|---|---|
| **Stronger** | ACIE and sovereign revenue exceeding Hyperscale in absolute terms; gross margin holding ≥75% through a memory up-cycle; largest customer share below 12%; supply commitments growing slower than revenue |
| **Weaker** | Gross margin below 70% without an identified mix cause; inventory provisions above 3% of revenue for two quarters; top-three customer share re-concentrating above 55%; a named hyperscaler disclosing majority-internal accelerator deployment |
| **Breaks** | Any guarantee moving from contingent disclosure to recognised liability; a supply-commitment cancellation charge above $10bn; two consecutive quarters of sequential Data Center revenue decline |

## 13. Open questions

Unit volumes, ASPs and content per rack — none disclosed, so no source can separate price from volume. Software, services and DGX Cloud revenue, never broken out. The identity of the 16%/15%/13% direct customers, and the "AI research and deployment company" the FY2026 10-K says contributed meaningfully through intermediaries. Dollar amounts of individual equity stakes. Maintenance versus growth capex. Whether the $105bn SB Energy cap can be sized net of the OpenAI indemnity, which the filing describes but does not quantify. The custom-silicon share of hyperscaler AI compute — not answerable from NVIDIA's filings at all.

## 14. Update log

| Date | Event / source | What changed | Impact on thesis |
|---|---|---|---|
| 7 Sep 2026 | Initial Coverage File created from 10-Ks FY2017–FY2026, 10-Qs through Q2 FY2027, 8-Ks through 3 Sep 2026, 2026 proxy | — | — |

## 15. Source map

| Document | Period / date | Used for |
|---|---|---|
| Form 10-K | FY2026, ended 25 Jan 2026 (filed 26 Feb 2026) | Business description, segments, supply chain, competition, FY2026 financials, customer concentration, capital allocation |
| Form 10-Q | Q2 FY2027, ended 26 Jul 2026 (filed 26 Aug 2026) | Latest financials, market-platform revenue, commitments and guarantees, other income, export-control status, buybacks and dividend |
| Form 10-Q | Q1 FY2027, ended 26 Apr 2026 (filed 20 May 2026) | Prior-period comparatives for the metrics table |
| Form 8-K, Item 1.01/2.03/7.01 | 17 Aug 2026 | SB Energy residual-value guarantees, PORTS Technology Campus terms |
| Form 8-K, Item 8.01 | 3 Sep 2026 | Hugging Face acquisition agreement and openness commitment |
| Form 8-K, Item 5.02 | 2 Jul 2026 | EVP Worldwide Field Operations succession |
| DEF 14A | Filed 12 May 2026 | Executive compensation structure, FY2026 goal adjustment and payouts, CEO ownership |
| Forms 10-K | FY2017–FY2025 | Long-run segment and comparability context |
| External market data | 4 Sep 2026 close | §8 market-data callout only |
