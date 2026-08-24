# Blockchain / Crypto Risk Note

## 1. What a "Paytm Crypto Insights" watchlist would need to get right

A hypothetical "Paytm Crypto Insights" watchlist — a read-only feature
letting retail users track crypto-asset prices inside the Paytm app,
short of enabling trading — still carries real responsibility for what it
implicitly legitimizes by listing an asset at all. Two things it must get
right before Paytm could responsibly surface it:

**Stablecoin type must be disclosed, not just price.** Fiat-collateralized
stablecoins (e.g. USDC-style designs) hold cash/short-term government
securities roughly 1:1 against issued tokens; their main risks are
custodial (does the issuer really hold what it claims, verified by regular
attestation) and redemption risk under stress. Algorithmic stablecoins
maintain their peg purely through code-based mint/burn incentives against
a companion volatile token, with no off-chain collateral backstop — when
confidence drops, the same mechanism meant to restore the peg can instead
accelerate a collapse (a reflexive "death spiral," as has happened to real
algorithmic designs). A watchlist that displays both types with an
identical "stablecoin" badge and no distinction actively misleads retail
users into treating an algorithmic stablecoin as a cash equivalent, which
it is not. Any Paytm-surfaced stablecoin listing must label the backing
mechanism explicitly and should exclude undercollateralized/algorithmic
designs from any framing that implies safety.

**Tokenomics and DAO governance risk must be surfaced per-asset, not
buried in a whitepaper link.** Two structural risks apply broadly: (a)
concentrated token supply / insider unlock schedules can let early holders
dump on retail liquidity that a watchlist just directed users toward, and
(b) DAO governance is frequently captured by large token-holders
("whale governance"), with no legal accountability structure comparable
to a regulated entity — so there is often no recourse when a governance
vote damages token holders. A responsible feature would need a
standardized per-asset risk panel (supply concentration, unlock schedule,
governance structure) shown alongside price, not price alone.

## 2. Crypto allocation recommendation for Paytm Money

Standard portfolio theory (CAPM and related frameworks) prices an asset by
its systematic risk relative to expected cash flows/dividends; crypto has
neither underlying cash flows nor dividends, so there is no fundamental
anchor for its "fair value" — its price is driven almost entirely by
sentiment and flow, not discounted cash flow economics. Four further
factors compound this for a retail advisory product specifically: (a)
crypto's correlation with traditional assets is low or negative in some
regimes but has repeatedly spiked toward 1 during liquidity-crisis
sell-offs — exactly when diversification benefit is needed most, it tends
to disappear; (b) returns are heavy-tailed and positively skewed at the
asset-class level (a few extreme winners), which flatters *aggregate*
crypto-market charts while the *median* individual token investor
experience is frequently a loss; (c) **survivorship bias** compounds this
directly — the charts retail users see are of the tokens that survived
and appreciated, not the very large number that went to zero and quietly
disappeared from every index; (d) transaction costs (spreads, custody,
on/off-ramp fees, gas) are materially higher than listed equities or
bonds, eating further into already-skewed expected returns.

**Recommendation: a maximum 2% allocation, and only for Aggressive-tier
investors who explicitly opt in — 0% (no allocation) as the system default
for Conservative and Moderate tiers.** This mirrors the escalation logic
already used in `advisory_agent.py`: crypto exposure should never be
auto-included in a standard recommendation, only offered as a small,
clearly-labeled satellite position with mandatory risk disclosure,
consistent with treating it as a speculative allocation rather than a
core portfolio holding.

## 3. T.A.N.G. framework — two most relevant vectors for Paytm

**Authority (highest-relevance vector).** A fraudster impersonates a
Paytm/bank "support executive" or "recovery officer," citing a fabricated
failed transaction, KYC lapse, or loan default, and pressures the victim
into reading out an OTP or entering their UPI PIN on what is framed as a
"verification" collect-request — across UPI, lending recovery calls, and
fake wealth-advisor calls alike. **Bank-side real-time defense:** a
transaction-risk engine that treats any UPI PIN entry occurring during or
immediately after a payee-initiated "collect request" as high-risk by
default — regardless of what the caller claims — and forces a cooling-off
/ explicit re-confirmation screen showing the true payee name before the
PIN is accepted. This is the same real-time scoring principle already
implemented for burner-account and velocity-attack detection in
`fraud_queries.sql` (Part 1), applied to the point of authorization rather
than after the fact.

**Greed (second-most-relevant vector).** "Guaranteed return" investment
tips or unrealistically cheap "pre-approved" loan offers pushed through
unsolicited SMS/WhatsApp links, exploiting the desire for outsized, fast
gains to bypass normal diligence — most damaging on the wealth side, where
victims are lured into sending funds to an unverified "advisor." **Bank-side
real-time defense:** real-time behavioral-anomaly scoring (the same
Isolation Forest-style approach used on `txn_behaviour.csv` in Part 2)
applied to first-time transfers toward newly-added payees that closely
follow an in-app link click or a large, sudden investment-app deposit —
auto-flagging the transfer for a manual confirmation step rather than
letting it clear instantly, which is precisely the window in which
greed-driven urgency would otherwise push it through unexamined.
