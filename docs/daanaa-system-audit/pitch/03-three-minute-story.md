# Three-Minute Story

Daanaa is my attempt to turn a messy real-world nonprofit discovery problem into a working product with clear governance.

The main challenge is that nonprofit trust is not a single number. Donors need context, nonprofits need fair treatment, and the system has to avoid overclaiming what public data can prove. I built Daanaa around public IRS and ProPublica data, peer comparisons, search, and nonprofit claim flows.

The platform architecture split into two major paths: a full backend for richer workflows and a production-edge backend for fast browse/search delivery. The data pipeline normalizes and indexes public records, while the frontend presents the results in a way that is supposed to be useful without pretending to certify worth.

AI assisted me in the building process. I used it as a research and drafting partner, and I treated it as part of a human-governed process rather than the decision-maker. The codebase reflects that distinction: some steps are deterministic, some are AI-assisted, and some require explicit human review.

What I learned is that the hard part is not just building the software. It is making sure the public language, the technical implementation, and the governance model all stay aligned.

