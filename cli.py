#!/usr/bin/env python3
import argparse
import dns.resolver

def resolve_record(domain: str, rtype: str = "A"):
    try:
        answers = dns.resolver.resolve(domain, rtype)
        return [str(rdata) for rdata in answers]
    except Exception as e:
        return [f"Error: {e}"]

def main():
    parser = argparse.ArgumentParser(description="Minimal DNS recon tool")
    parser.add_argument("domain", help="Target domain, e.g. example.com")
    parser.add_argument("-t", "--type", default="A", help="Record type (A, AAAA, MX, NS, TXT)")
    args = parser.parse_args()

    results = resolve_record(args.domain, args.type)
    for r in results:
        print(r)

if __name__ == "__main__":
    main()
