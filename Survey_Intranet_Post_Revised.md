# Order Process Survey: How Customers Buy

See Appendix for individual responses.

We surveyed 1,459 visitors on mcmaster.com from May 13 to 15, 2026, to understand how customers move from finding a part to placing an order. The picture across roles is consistent: customers describe the checkout itself as fast and reliable, and the friction lives in the workflow that surrounds it. Orders pass between requesters, buyers, and approvers; cart contents get retyped into procurement systems; the requester loses sight of the order once someone else takes over; and teammates sharing a single login describe carts that overwrite each other. Customers shared a preference for McMaster-Carr to extend into that workflow without changing the catalog experience they already rely on.

## Most orders pass through more than one person

A majority of customers don't own the order from end to end. 59% find a part and place the order themselves; the other 41% participate in a split workflow where one person finds the part and another places the order. The handoff concentrates in two roles: Engineers/Designers send the cart to a buyer in 38% of cases, and customers in Purchasing/Procurement place orders built by someone else 32% of the time.

| Role | Self-serve | Hands off to buyer | Places for others | It depends |
|---|---|---|---|---|
| Engineer / Designer | 55% | **38%** | <1% | 6% |
| Maintenance / Operations | 66% | 24% | 3% | 6% |
| Purchasing / Procurement | 55% | 1% | **32%** | 12% |
| Other | 68% | 10% | 9% | 12% |

The 8% who selected "It depends" describe the most common reality in industry — several patterns coexist depending on the dollar amount, the project, or who is available that day.

> "Pretty much all of the above. Sometimes a person finds the product and places the order themselves, sometimes someone asks for the product and someone else finds it and places the order. Most of the time…"
> – Engineer

> "I don't really do the buying — I'm more of a find-a-part type of guy. I send the parts I found to my manager, who approves the item and directs me to create a purchase request, or he'll just order it on his credit card."
> – John Laskey, Engineer at Calnetix Technologies

> "Machine-specific parts are ordered through the manufacturer. Websites I have accounts on, such as McMaster-Carr, Uline, or Grainger, I order myself. Websites I do not have accounts with, I send links to purchasing."
> – Maintenance/Operations

## Approvals are common, and the gate is usually a dollar threshold

54% of customers say their orders require approval at least some of the time, and the approval gate is role-neutral — 58% of Engineers/Designers, 56% of Maintenance/Operations, and 52% of Purchasing/Procurement face it. Where customers said "Sometimes" and wrote in an explanation, 70% pointed to a price threshold. 87 customers shared an explicit dollar amount, and the values cluster tightly at $500, $1,000, and $5,000.

| Order under $X | Can place without approval (n=87) | % of explicit thresholds |
|---|---|---|
| Under $50 | 87 | 100% |
| Under $500 | 79 | 91% |
| **Under $1,000** | **58** | **67%** |
| **Under $2,000** | **36** | **41%** |
| Under $5,000 | 20 | 23% |
| Under $10,000 | 6 | 7% |

The frustration customers describe is rarely the approval itself — it's the time the approval takes, the second system it lives in, and the workaround it forces. The most common workaround is a company credit card used to step around the slower internal process.

> "We purchase most things from McMaster-Carr using Pro Cards. We do that because the internal Purchasing structure we have is too slow to be efficient for our particular needs. We are an R&D shop working within a State institution. Therefore, the protocols they use won't work."
> – Engineer at The University of Texas at Austin

> "Federal Government procurement takes forever as a second person (with no knowledge or understanding of my requirement) must verify that the items I'm ordering from McMaster are NOT available at any of the preapproved mandatory sources/vendors."
> – Engineer

> "The amount of times I have to order. If maintenance techs can place their own orders and I just approve, that would be great."
> – Maintenance/Operations

391 customers said they would use "Send orders for approval" on McMaster, more than twice the 169 who say they use it on another supplier's site today.

## Handing an order off usually means re-entering it

When the cart moves from the person who found the part to the person who places the order, the most common path is email. 42% of customers who hand off do so by email, typically by pasting part numbers, descriptions, and quantities into a separate requisition form. 32% submit the order through a procurement system — SAP, Coupa, Ariba, Epicor, Oracle, D365, or JD Edwards — which usually requires re-entering the same information a second time before a purchase order is generated. 30% use McMaster's "Send cart" feature, and 12% share a single company login.

| Handoff mode | n | % of customers who hand off |
|---|---|---|
| Email | 257 | **42%** |
| Procurement system (SAP, Coupa, Ariba…) | 199 | **32%** |
| Send cart from mcmaster.com | 183 | **30%** |
| In person / over the phone | 103 | 17% |
| Shared cart on the same account | 76 | 12% |
| Other | 53 | 9% |

The "Other" write-ins point at the lengths customers go to in order to bridge McMaster to the rest of their workflow: a Slack channel that triggers a Kanban card, a JIRA board, a Smartsheet integration, a copied cart link pasted into a purchasing portal, a piece of paper handed to the buyer.

The retyping shows up plainly in the next question. 72% of customers (excluding "not sure") say product information is re-entered into another system at least some of the time. The work is concentrated in Purchasing — 77% of Purchasing/Procurement customers say they're re-entering McMaster data, and when re-entry happens, a buyer is doing it 50% more often than the requester themselves.

> "I have to manually input McMaster's item information into our procurement system. There's a lot of manual copy-paste of information from McMaster's website into Oracle procurement system. It's time consuming and error prone."
> – Brian Rolley, Engineer at Arconic

> "Having to enter in everything into our SAP system. I have to put in quantities, part numbers, prices, links to your products… all of that info is already in my cart. We used to just share carts with purchasing, but now they have implemented SAP. I've told them that McMaster likely has the ability to integrate with our SAP — help me convince them!"
> – Boone Cruse, Maintenance at Noveon Magnetics

> "Re-entering into our ASI system all of the notes and details so that the purchaser can correctly select and order my list of items. It can take upwards to an hour if it's a long list of hardware for a new project."
> – Engineer at Waterous Co

When a punchout is already in place, customers describe it as a relief — and they tell us when it isn't working, in equally clear terms.

> "We use Coupa, and I love how McMaster's site plugs into Coupa. I am able to check out my cart and it automatically populates all of the items into my Coupa cart. The bad part is that I have to go in and manually change every line item to the correct account and cost center. I am not able to bulk change the items. So I have to manually do it one by one."
> – Engineer at BD

> "When punchout connection to Coupa fails the entire cart is lost."
> – Engineer at AbCellera

Per-line cost-center and job-code tagging at cart-build time is the workaround customers ask for most often when their punchout is otherwise working. 476 said they would use it on McMaster (304 regularly). Customers also called out a list of systems by name they'd like McMaster to talk to directly: SAP, Coupa, Ariba, Epicor, Oracle, D365, JD Edwards, Precoro, Fulcrum Pro, and Paperless Parts.

> "We would love a direct integration with Fulcrum Pro (our ERP system). It would save us considerable time on a daily basis."
> – Owner at Elemetal Fabrication and Machine

> "Amazon has a setup that I can make a cart and then go into our procurement system and the cart is still there and it's the best. Something like this would be great."
> – Manager

## Once an order is handed off, the requester loses sight of it

The most-wanted feature in the entire survey is the simplest one. 694 customers said they would use "Share order status with others" on mcmaster.com — 47% of the entire sample, and almost twice the count for any other feature. Today, the status emails that follow an order go to the buyer who placed it; the requester chasing the part has no direct way to see whether it's been ordered, shipped, or received.

This result was the most surprising to us going in. We expected the heaviest demand to fall on heavier procurement features. Instead, customers are asking for transparency on the order they already submitted, and the open responses make the gap concrete:

> "The visibility of ordering status. I want to know if something's been ordered, when it was ordered, has it shipped, when will it arrive, when it has arrived — all without having to rely on someone else giving me this information."
> – Project Manager

> "The person adding the items to the cart (submitting order for approval) does not get any of the information about the orders — it only goes to the buyer (person approving the order). This means a lot of extra chatting with McMaster reps to gain information that's already been made available (tracking, order confirmation, MTRs, etc)."
> – Fabrication Shop at Redwood Materials

> "I don't have access to the engineering McMaster account, so I cannot see tracking and I am not up to date on what gets ordered. If people have questions, I cannot retrieve the information to answer them."
> – Engineer at Kalwall

The neighboring features in the list tell the same story from the other direction. 528 customers want to add teammates to their account and 353 want defined roles like requester, buyer, and approver — both of which describe the same gap. Our web support team hears these requests regularly, often phrased as "can I add a coworker who can see my orders." 497 customers want to attach a purchase order to a cart, which today is a manual step on both sides of the handoff.

## Shared accounts create cart conflicts

12% of customers who hand off told us they share one McMaster login with their team — and 11% of the open frustration responses describe what happens next. When several teammates work out of the same cart, items overwrite each other, items disappear before they're placed, no one can tell who added what, and a punchout failure can wipe the cart entirely.

> "Multiple users using the same account and carts overwriting others… when I log in it overwrites the cart that had previously been started. This is the BIGGEST annoyance."
> – Corey Holland, Maintenance at Wonder/Sweetgreen (MMF 1469675001)

> "We have 2, sometimes 3 people who add to our cart on the same account. The problem is the carts are separated and then the person who finalizes and places the order at the end of the day has to transfer from multiple spots into one cart. And we can't always see what the other person has added unless we go to the history tab."
> – Purchasing/Procurement at Rocky Mountain Twist

> "Most days, more than 2-3 people need to place orders, so we make a slack thread and then add stuff, and the one person forgets to place it half the time. We've gone as far as trying to make slack bots or Chrome extensions to auto-place at 6:59 or something like this… Ideally we'd just add to one big company cart that would order automatically."
> – Engineer at Nudge

> "Accidentally erasing others' shopping carts when I sign in to our group account."
> – Nick Foley, Engineer at Seneca

Customers describe the shared login as a workaround for the missing teammate model. What they ask for instead is named users under one company account, with each cart action attributed to the person who took it.

> "We currently have several users signed in with the same username and password. Engineers, purchasers, and management. We would like to create additional users for the same account if possible."
> – Purchasing/Procurement at Burgi Corporation

> "Sub-accounts that can be assigned to teams within the company and a central cart that automatically adds the name of the sub-account that added it would be good."
> – Engineer

A smaller group described the opposite gap — they want carts they can keep separate per project, save as a template for repeated orders, or build alongside an open cart without losing it. "Save for later" is the workaround customers cite most often.

> "I need to build and place orders for multiple projects simultaneously, and those purchases need to be made separately for billing purposes. Only having one cart means I constantly have to save things for later, or open them in a new tab to remember them."
> – Engineer at Swope Design Solutions

## Customers want McMaster to extend into the workflow they already have

The feature interest grid in question 7 makes the pattern explicit. For every feature we asked about, the count of customers who would use it on mcmaster.com is two to three times the count who say they use it on another supplier's site today. Customers aren't asking us to catch up — they're asking us to lead.

| Feature | Currently use elsewhere | Would use on McMaster (Regularly + Occasionally) | Of those, Regularly |
|---|---|---|---|
| Share order status with others | 200 | **694** | 337 |
| Add teammates to your account | 240 | 528 | 288 |
| Attach purchase orders | 231 | 497 | 300 |
| Assign account / job / cost-center codes | 184 | 476 | 304 |
| Connect with procurement system | 133 | 397 | 286 |
| Send orders for approval | 169 | 391 | 223 |
| Set roles (requester / buyer / approver) | 98 | 353 | 187 |

Two things stand out in this result. The first is that the top of the list isn't heavy procurement tooling — it's transparency and teammates. The requester losing sight of the order, and the team that can't get on one account, are what customers describe as the most acute gap. The second is that "Connect with procurement system" is fifth on the list, even though data re-entry is the most concretely described frustration in the open responses. The reading we take from this is that customers want in-app workflow tools first, and deeper procurement integration as a parallel track.

The thresholds for an in-app approval flow are already legible in the survey. Customers gravitate toward "buy under $X without approval, send for approval above $X," and the dollar amounts cluster at $500, $1,000, and $5,000. The teammate model customers describe is named users under one company account, with per-line authorship on the cart. The integration model they describe is more punchout coverage with graceful failure, plus bulk cost-center tagging that survives the handoff to ERP.

The clearest signal in the data is also the most encouraging. Almost every frustration was paired with a love note for the catalog itself. Customers aren't asking us to change what we already do well — they're asking us to extend a little further into the workflow that begins where the catalog ends.

> "Been in Engineering for over 40 years — McMaster-Carr is by far the best most user-friendly catalog/order-placing site I have seen."
> – Engineer at Storion Energy

> "Our supply chain utilizes eCatalogs with a few vendors. Where they do, the ordering process is somewhat faster, when it works. When I purchase from McMaster-Carr, I have to input each item manually and send the PR on for approval to get turned into a PO. Even with that process, I much prefer McMaster-Carr over Grainger."
> – Maintenance/Operations at DTE Energy

*[Authors]*

---

# Appendix — Sample Individual Responses

1,459 responses | May 13, 2026 to May 15, 2026

The following responses are a representative sample of the patterns described above. The full export is available in Qualtrics.

---

**Corey Holland | Wonder/Sweetgreen | Maintenance/Operations | Marketed #1**

MMF: 1469675001

**Buying scenario:** I find products and place the order myself.

**Approval needed:** Sometimes

**Handoff mode:** Shared cart on the same account used by many teammates

**Re-enters product details:** Yes, sometimes

**Most frustrating part of buying process:**
Multiple users using the same account and carts overwriting others… when I log in it overwrites the cart that had previously been started. This is the BIGGEST annoyance.

**Anything else to share:**
Please fix carts overwriting each other, pretty please, with sugar on top.

---

**Brian Rolley | Arconic | Engineer/Designer | Marketed #2**

**Buying scenario:** I find products, and someone else places the order.

**Approval needed:** Yes

**Handoff mode:** Submitted in our procurement or approval system (Oracle)

**Handoff content:** Pre-built cart, Notes

**Re-enters product details:** Yes, frequently

**Most frustrating part of buying process:**
I have to manually input McMaster's item information into our procurement system. There's a lot of manual copy-paste of information from McMaster's website into Oracle procurement system. It's time consuming and error prone.

---

**Boone Cruse | Noveon Magnetics (Urban Mining Company) | Maintenance/Operations | Marketed #3**

**Buying scenario:** I find products and place the order myself.

**Approval needed:** Yes

**Handoff mode:** Submitted in our procurement or approval system (SAP)

**Re-enters product details:** Yes, frequently

**Most frustrating part of buying process:**
Having to enter in everything into our SAP system. I have to put in quantities, part numbers, prices, links to your products… all of that info is already in my cart. We used to just share carts with purchasing, but now they have implemented SAP. I've told them that McMaster likely has the ability to integrate with our SAP… Help me convince them!

---

**John Laskey | Calnetix Technologies | Engineer/Designer | Unknown #4**

**Buying scenario:** It depends.

**It depends explanation:**
I don't really do the buying — I'm more of a find-a-part type of guy. I send the parts I found to my manager, who approves the item and directs me to create a purchase request, or he'll just order it on his credit card.

**Approval needed:** Sometimes

**Re-enters product details:** Yes, sometimes

---

**Engineer at Allient | Engineer/Designer | Unknown #5**

**Buying scenario:** I find products, and someone else places the order.

**Approval needed:** Yes

**Handoff mode:** Email, Submitted in our procurement or approval system (D365)

**Handoff content:** Pre-built cart, Notes

**Re-enters product details:** Yes, frequently

**Most frustrating part of buying process:**
Our company requires signed Excel purchase requisitions when ordering through MMC. I copy-paste the MMC table view into the Excel form, then email the cart to myself, copy the link into my Excel form, then forward it to my manager who approves and submits it to purchasing; purchasing opens the cart with the link, places the order, then goes into D365 and enters accounting info. If an order has only one cost center, they can enter an overall expense for that one cost center — but if my order includes parts for multiple cost centers, they have to manually enter the cost of each line item. For this reason, they are not thrilled when I submit an order for ~30 line items.

---

**Engineer at Storion Energy | Engineer/Designer | Unknown #6**

**Buying scenario:** I find products, and someone else places the order.

**Approval needed:** Yes

**Handoff mode:** Email, Submitted in our procurement or approval system (Precoro)

**Re-enters product details:** No, information flows through without needing to re-enter it

**Most frustrating part of buying process:**
Been in Engineering for over 40 years — McMaster-Carr is by far the best most user-friendly catalog/order-placing site I have seen. Presently McMaster-Carr is set up in our procurement system 'Precoro'. The Engineer completes his MMC cart with Purchaser on shared/email distribution. The Purchaser opens up Precoro, selects the McMaster-Carr radio button and the MMC cart automatically populates the Purchase Request order form. The only thing the Purchaser has to do is add accounting info.

---

**Engineer at BD | Engineer/Designer | Marketed #7**

**Buying scenario:** I find products and place the order myself.

**Approval needed:** Sometimes

**Handoff mode:** Submitted in our procurement or approval system (Coupa)

**Re-enters product details:** Yes, sometimes

**Most frustrating part of buying process:**
We use Coupa, and I love how McMaster's site plugs in to Coupa. I am able to check out my cart and it automatically populates all of the items into my Coupa cart. The bad part is that I have to go in and manually change every line item to the correct account and cost center. I am not able to bulk change the items. So I have to manually do it one by one.

---

**Owner at Elemetal Fabrication and Machine | Other (Owner) | Unknown #8**

**Buying scenario:** I find products and place the order myself.

**Re-enters product details:** Yes, frequently

**Most frustrating part of buying process:**
We would love a direct integration with Fulcrum Pro (our ERP system). It would save us considerable time on a daily basis.

---

**Purchasing at Burgi Corporation | Purchasing/Procurement | Unknown #9**

**Buying scenario:** Someone else finds products, and I place the order.

**Handoff mode:** Shared cart on the same account used by many teammates

**Most frustrating part of buying process:**
We currently have several users signed in with the same username and password. Engineers, purchasers, and management. We would like to create additional users for the same account if possible.

---

**Engineer at Swope Design Solutions | Engineer/Designer | Marketed #10**

**Buying scenario:** I find products and place the order myself.

**Most frustrating part of buying process:**
I need to build and place orders for multiple projects simultaneously, and those purchases need to be made separately for billing purposes. Only having one cart means I constantly have to save things for later, or open them in a new tab to remember them.

---

**Engineer at Nudge | Engineer/Designer | Unknown #11**

**Buying scenario:** I find products and place the order myself.

**Handoff mode:** Shared cart on the same account, Email (Slack thread)

**Most frustrating part of buying process:**
Most days, more than 2-3 people need to place orders, so we make a slack thread and then add stuff, and the one person forgets to place it half the time. We've gone as far as trying to make slack bots or Chrome extensions to auto-place at 6:59 or something like this… Ideally we'd just add to one big company cart that would order automatically.

---

**Fabrication Shop at Redwood Materials | Other (Fabrication) | Unknown #12**

**Buying scenario:** I find products, and someone else places the order.

**Approval needed:** Yes

**Most frustrating part of buying process:**
The person adding the items to the cart (submitting order for approval) does not get any of the information about the orders — it only goes to the buyer (person approving the order). This means a lot of extra chatting with McMaster reps to gain information that's already been made available (tracking, order confirmation, MTRs, etc).
