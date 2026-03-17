#!/usr/bin/env python3
import argparse
import dns.exception
import dns.query
import dns.rdatatype
import dns.zone
import dns.resolver

def resolve_record(domain: str, rtype: str = "A"):
    try:
        answers = dns.resolver.resolve(domain, rtype)
        return [str(rdata) for rdata in answers]
    except Exception as e:
        return [f"Error: {e}"]

def attempt_zone_transfer(domain: str, nameserver: str, timeout: float = 5.0):
    try:
        xfr = dns.query.xfr(nameserver, domain, timeout=timeout, lifetime=timeout)
        zone = dns.zone.from_xfr(xfr, relativize=False)
        if zone is None:
            return None, "No zone data returned"
        return zone, None
    except dns.exception.FormError as e:
        return None, f"FormError: {e}"
    except dns.exception.Timeout:
        return None, "Timeout"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"

def nameservers_for_domain(domain: str):
    try:
        answers = dns.resolver.resolve(domain, "NS")
        return [str(rdata).rstrip(".") for rdata in answers]
    except Exception:
        return []

def main():
    parser = argparse.ArgumentParser(description="Minimal DNS recon tool")
    parser.add_argument("domain", help="Target domain, e.g. example.com")
    parser.add_argument(
        "-t",
        "--type",
        default="A",
        help="Record type (A, AAAA, MX, NS, TXT)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show extra information about the query",
    )
    parser.add_argument(
        "--axfr",
        action="store_true",
        help="Attempt DNS zone transfer (AXFR) from authoritative nameservers (authorized testing only)",
    )
    parser.add_argument(
        "--ns",
        dest="nameserver",
        help="Nameserver to try for AXFR (IP or hostname). If omitted, NS records will be discovered.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Network timeout seconds (default: 5.0)",
    )
    args = parser.parse_args()

    if args.axfr:
        targets = [args.nameserver] if args.nameserver else nameservers_for_domain(args.domain)
        if not targets:
            print("[-] No nameservers found to try for AXFR")
            return

        for ns in targets:
            if args.verbose:
                print(f"[+] Trying AXFR {args.domain} @ {ns}")
            zone, err = attempt_zone_transfer(args.domain, ns, timeout=args.timeout)
            if err:
                if args.verbose:
                    print(f"[-] AXFR failed @ {ns}: {err}")
                continue

            print(f"[+] AXFR succeeded @ {ns}")
            for (name, node) in zone.nodes.items():
                for rdataset in node.rdatasets:
                    for rdata in rdataset:
                        owner = str(name)
                        if owner == "@":
                            owner = zone.origin.to_text(omit_final_dot=False)
                        elif not owner.endswith("."):
                            owner = f"{owner}.{zone.origin.to_text(omit_final_dot=False)}"
                        rtype = dns.rdatatype.to_text(rdataset.rdtype)
                        ttl = rdataset.ttl
                        print(f"{owner}\t{ttl}\tIN\t{rtype}\t{rdata}")
            return

        print("[-] AXFR did not succeed against any tried nameserver")
        return

    if args.verbose:
        print(f"[+] Querying {args.type} records for {args.domain}")

    results = resolve_record(args.domain, args.type)
    for r in results:
        print(r)

if __name__ == "__main__":
    main()
