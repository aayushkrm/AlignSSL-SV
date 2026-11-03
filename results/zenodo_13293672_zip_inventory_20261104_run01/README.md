# Remote ZIP central-directory inventory

The [study note](../../docs/research/2026-11-04-independent-callset-inventory.md)
describes this public 15.2 GB archive and the decision not to infer variant
content from its member names. `inventory.json` lists all 1,101 central
directory entries, HTTP HEAD fields and four byte-range requests. The reader
transferred 148,023 bytes, not the full archive. The publisher's whole-archive
MD5 and the members' CRCs have **not** been verified.

Reproduce with Python 3 and a new output path:

```sh
python analysis/inventory_remote_zip.py \
  --url 'https://zenodo.org/records/13293672/files/1100VCF.zip?download=1' \
  --output /tmp/remote-vcf-zip-inventory-new
```

The runner accepts only correct HTTP 206 responses, checks the exact requested
Content-Range, and refuses to transfer more than 8 MiB by default. Because the
observed responses lacked an ETag, neither the recorded range metadata nor
the partial transfer is a full immutable archive identity check.
