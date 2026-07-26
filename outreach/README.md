# Science-popular note

A lay-audience account of the AlignSSL-SV results, written to the six-part
structure of the project curator's guide (title/abstract, project, known
results, our results, team process, plans).

## Build

```
python make_formulas.py     # eq1_tensor.png, eq2_loss.png (mathtext, 400 dpi)
python make_schematic.py    # note_fig1_schematic.png
python make_results_fig.py  # note_fig2_results.png
python make_fig3.py         # note_fig3_standings.png
python build_note.py        # AlignSSL_SV_popular_note.docx
```

Every number quoted in the note and every bar and point in the three figures
is read at build time from `../results/*.csv` — nothing is transcribed by
hand. The figure scripts open `table1_label_efficiency.csv`,
`table6_single_feature_auc.csv`, `table7_hardneg_label_efficiency.csv` and
`table9_hardneg_single_feature_auc.csv` directly.

Formulas are rendered as 400-dpi images rather than typed as text, per the
brief. The document uses a single font throughout, justified body text,
captioned figures, and heading levels 1-2.
