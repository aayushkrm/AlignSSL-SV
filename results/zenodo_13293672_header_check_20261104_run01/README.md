# Four selected remote VCF headers

The [selection and result](../../docs/research/2026-11-04-independent-callset-inventory.md)
were recorded before reading these four headers. `headers.json` includes
selected source/reference/annotation lines, header and compressed-prefix
hashes, all byte ranges and incomplete-source limits. Only header lines were
inspected and retained. The compressed prefixes can contain record bytes,
and gzip may decompress past the header internally. The prefixes were not
retained. The data are not representative of all 1,100
members, and the full member CRCs and ZIP MD5 have not been checked.

With the prior inventory packet available, reproduce via:

```sh
python -m analysis.inspect_remote_zip_vcf_headers \
  --inventory results/zenodo_13293672_zip_inventory_20261104_run01/inventory.json \
  --output /tmp/remote-vcf-headers-new
```

The code verifies the frozen entry names against each local ZIP header, limits
each member prefix to 256 KiB and the full run to 8 MiB, and requires the
current archive length and Last-Modified HEAD value to match the inventory.
That is not a substitute for a whole-archive checksum or an immutable ETag.
