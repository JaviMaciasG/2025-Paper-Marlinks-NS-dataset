.PHONY: main $(FLS_FILE) paper.zip ### clean

BASENAME  = paper
TEX_FILE  = $(BASENAME).tex
PDF_FILE  = $(BASENAME).pdf
PDF_TOOL=pdflatex
BIBLIO_TOOL=bibtex

ORIGINAL_FLATTEN_TEX_FILE = ../original/$(BASENAME)-flatten-v1.tex
ORIGINAL_BIB_FILE = ../original/$(BASENAME).bbl
FLATTEN_TEX_FILE = $(BASENAME)-flatten.tex
DIFF_FLATTEN_BASENAME = $(BASENAME)-flatten-diff
DIFF_FLATTEN_TEX_FILE = $(DIFF_FLATTEN_BASENAME).tex

LATEXDIFF_OPTIONS="--exclude-textcmd=\"hskip,vskip,smallskip,medskip,bigskip\""
FLAGS_SYNCTEX_PDFLATEX=-synctex=1

### --- Añadidos para latexmk + dependencias automáticas ---
LATEXMK = latexmk
LATEXMK_OPTS = -pdf -interaction=nonstopmode -file-line-error -use-make -recorder
LATEXMK_OPTS += -pdflatex='pdflatex -synctex=1 %O %S'   ### Synctex vía latexmk
DEPFILE = $(BASENAME).d
-include $(DEPFILE)
### --------------------------------------------------------

all: $(PDF_FILE)

### Compilación con latexmk + generación de dependencias reales
$(PDF_FILE): $(TEX_FILE)
	$(LATEXMK) $(LATEXMK_OPTS) -deps -deps-out=$(DEPFILE) $(BASENAME)

flatten:
	latexpand $(TEX_FILE) > $(FLATTEN_TEX_FILE)

latexdiff: flatten
	latexdiff $(LATEXDIFF_OPTIONS) $(ORIGINAL_FLATTEN_TEX_FILE) $(FLATTEN_TEX_FILE) >  $(DIFF_FLATTEN_TEX_FILE)
	$(PDF_TOOL) $(FLAGS_SYNCTEX_PDFLATEX) $(DIFF_FLATTEN_TEX_FILE)
	latexdiff $(LATEXDIFF_OPTIONS) $(ORIGINAL_BIB_FILE) $(BASENAME).bbl > $(DIFF_FLATTEN_BASENAME).bbl
	sed -i 's/\\DIFadd{1em plus 0\.5em minus 0\.4em}/1em plus 0.5em minus 0.4em/g' $(DIFF_FLATTEN_BASENAME).bbl
#	$(BIBLIO_TOOL) $(DIFF_FLATTEN_BASENAME)
	$(PDF_TOOL) $(FLAGS_SYNCTEX_PDFLATEX) $(DIFF_FLATTEN_TEX_FILE)
	$(PDF_TOOL) $(FLAGS_SYNCTEX_PDFLATEX) $(DIFF_FLATTEN_TEX_FILE)
#	rubber -d $(DIFF_FLATTEN_TEX_FILE)

zip: paper.zip
#	zip paper.zip Makefile *.tex figures/* *.bib *.cls *.sty logo-eps-converted-to.pdf

# Asegura que existe el .d con todas las dependencias reales
$(DEPFILE): $(TEX_FILE)
	$(LATEXMK) $(LATEXMK_OPTS) -deps -deps-out=$(DEPFILE) $(BASENAME)

# Build paper2.zip from the deps file, keeping only project-local, existing files
paper.zip: $(DEPFILE)
	@echo "Collecting inputs from $(DEPFILE)..."
	@sed -e ':a' -e 'N' -e 's/\\\n/ /' -e 'ta' $(DEPFILE) \
	  | sed 's/^[^:]*:[[:space:]]*//' \
	  | tr ' ' '\n' \
	  | sed 's|^\./||' \
	  | grep -v '^[[:space:]]*$$' \
	  | grep -v '^/' \
	  | grep -v '^\.\./' \
	  | sort -u > .zip.candidates
	@while read f; do [ -f "$$f" ] && echo "$$f"; done < .zip.candidates > .zip.list
	@test -s .zip.list || { echo "No project-local inputs found in $(DEPFILE)."; rm -f .zip.candidates .zip.list; exit 12; }
	@echo "Makefile" >> .zip.list
	@zip -@ $@ < .zip.list
	@rm -f .zip.candidates .zip.list
	@echo "Created $@ with project files only."

### Limpieza sin rubber: usa latexmk -C y borra artefactos auxiliares
clean:
	$(LATEXMK) -C $(BASENAME)
	rm -f $(DEPFILE) paper.zip .deps.lst .deps.lst.tmp \
	      $(DIFF_FLATTEN_BASENAME).aux $(DIFF_FLATTEN_BASENAME).bbl \
	      $(DIFF_FLATTEN_BASENAME).blg $(DIFF_FLATTEN_BASENAME).log \
	      figures/*converted-to.pdf

