App Name: OrderTrack
Core capabilities: capture orders, update status, notify customers
Users: internal ops, customers (read-only)
Traffic: peak 150 rps, avg 30 rps
Data: orders (~200GB/yr), events, customer profiles
NFR: 99.9% availability, P95 < 300ms read, < 800ms write
Compliance: PCI-DSS for payment tokens, PII handling
Current: monolith (Python Flask), MySQL, cron batch emails
