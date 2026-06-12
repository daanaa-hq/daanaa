# DNS Setup — daanaa.org

Status (2026-06-11): Steps 1, 2, 4, 5 are live. **Step 3 (DKIM) is NOT done** —
`google._domainkey.daanaa.org` is empty, so all mail sent as @daanaa.org fails
DMARC and our own p=quarantine policy sends it to spam (observed with claim
confirmation emails). Complete Step 3 before any org-facing email goes out.

Current state (2026-06-01): daanaa.org resolves to 192.64.119.16 (registrar parking).
Target: point to the Ryzen server + configure email authentication.

Server IP: check with `curl ifconfig.me` on the ecomargins box (currently at 192.168.1.73 on LAN).

---

## Step 1 — Point daanaa.org to your server

At your DNS provider (wherever daanaa.org is registered), add:

```
Type    Name    Value                   TTL     Proxy
A       @       <YOUR_SERVER_IP>        Auto    DNS only (grey cloud to start)
A       www     <YOUR_SERVER_IP>        Auto    DNS only
CNAME   *       daanaa.org              Auto    DNS only
```

Replace `<YOUR_SERVER_IP>` with the output of `curl ifconfig.me` on the server.

Once HTTPS is confirmed working on the server, enable Cloudflare proxy (orange cloud).

---

## Step 2 — SPF (prevents spoofing on send)

Add this TXT record:

```
Type    Name    Value
TXT     @       v=spf1 include:_spf.google.com ~all
```

Why `include:_spf.google.com`: the email agent sends via Google Workspace SMTP
(hello@ecomargins.com, with send-as aliases for @daanaa.org). This authorizes
Google's mail servers to send on behalf of daanaa.org.

---

## Step 3 — DKIM (cryptographic signature, prevents tampering)

In Google Workspace Admin → Apps → Google Workspace → Gmail → Authenticate email:
1. Click "Generate new record" for daanaa.org
2. Copy the TXT record Google gives you (looks like `google._domainkey`)
3. Add it to DNS:

```
Type    Name                    Value
TXT     google._domainkey       v=DKIM1; k=rsa; p=<Google-generated-key>
```

---

## Step 4 — DMARC (policy: what to do with unauthenticated mail)

Add this TXT record:

```
Type    Name        Value
TXT     _dmarc      v=DMARC1; p=quarantine; rua=mailto:trust@daanaa.org; ruf=mailto:security@daanaa.org; fo=1
```

This sends DMARC aggregate reports to trust@ (data team sees spoofing attempts)
and forensic reports to security@ (security team). p=quarantine means unauthenticated
mail goes to spam rather than being rejected outright (safer rollout than p=reject).

---

## Step 5 — MX records (for Google Groups receiving)

If not already set (check with `dig MX daanaa.org`):

```
Type    Name    Priority    Value
MX      @       1           aspmx.l.google.com
MX      @       5           alt1.aspmx.l.google.com
MX      @       5           alt2.aspmx.l.google.com
MX      @       10          alt3.aspmx.l.google.com
MX      @       10          alt4.aspmx.l.google.com
```

---

## Verification commands (run after DNS propagates, ~30 min)

```bash
# SPF
dig TXT daanaa.org | grep spf

# DKIM
dig TXT google._domainkey.daanaa.org

# DMARC
dig TXT _dmarc.daanaa.org

# A record
dig A daanaa.org

# MX
dig MX daanaa.org

# Test send-as by sending a test email from the agent:
cd ~/meritgiving && source venv/bin/activate && python3 -m scripts.email_agent.run --dry-run
```

---

## After DNS is live

1. Update API to serve `/.well-known/security.txt` (or copy from `coming-soon/.well-known/`)
2. Enable Cloudflare proxy (orange cloud) + SSL/TLS → Full (strict)
3. Update `LAUNCH-CHECKLIST.md` G3 DNS gate as done
