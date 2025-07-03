.PHONY: main $(FLS_FILE) paper.zip

BASENAME  = paper
TEX_FILE  = $(BASENAME).tex
FLS_FILE  = $(BASENAME).fls
PDF_FILE  = $(BASENAME).pdf
BIB_FILES = $(wildcard *.bib)
FIG_FILES = $(wildcard figures/*.bib)
PDF_TOOL=pdflatex
BIBLIO_TOOL=bibtex

ORIGINAL_FLATTEN_TEX_FILE = ../original/$(BASENAME)-flatten-v0.tex
ORIGINAL_BIB_FILE = ../original/$(BASENAME).bbl
FLATTEN_TEX_FILE = $(BASENAME)-flatten.tex
DIFF_FLATTEN_BASENAME = $(BASENAME)-flatten-diff
DIFF_FLATTEN_TEX_FILE = $(DIFF_FLATTEN_BASENAME).tex

FLAGS_SYNCTEX_PDFLATEX=-synctex=1


all: $(PDF_FILE)

$(PDF_FILE): $(TEX_FILE) $(BIB_FILES) $(FIG_FILES)
	echo "Processing LaTeX code with $(PDF_TOOL)"
	echo "Processing bibliography with $(BIBLIO_TOOL)"
	$(PDF_TOOL) $(FLAGS_SYNCTEX_PDFLATEX) $(BASENAME)
	$(BIBLIO_TOOL) $(BASENAME)
	$(PDF_TOOL) $(FLAGS_SYNCTEX_PDFLATEX) $(BASENAME)
	$(PDF_TOOL) $(FLAGS_SYNCTEX_PDFLATEX) $(BASENAME)


flatten:
	latexpand $(TEX_FILE) > $(FLATTEN_TEX_FILE)

latexdiff: flatten
	latexdiff $(ORIGINAL_FLATTEN_TEX_FILE) $(FLATTEN_TEX_FILE) >  $(DIFF_FLATTEN_TEX_FILE)
	$(PDF_TOOL) $(FLAGS_SYNCTEX_PDFLATEX) $(DIFF_FLATTEN_TEX_FILE)
	latexdiff $(ORIGINAL_BIB_FILE) $(BASENAME).bbl > $(DIFF_FLATTEN_BASENAME).bbl
#	$(BIBLIO_TOOL) $(DIFF_FLATTEN_BASENAME)
	$(PDF_TOOL) $(FLAGS_SYNCTEX_PDFLATEX) $(DIFF_FLATTEN_TEX_FILE)
	$(PDF_TOOL) $(FLAGS_SYNCTEX_PDFLATEX) $(DIFF_FLATTEN_TEX_FILE)
#	rubber -d $(DIFF_FLATTEN_TEX_FILE)

latexdiff-pdf:
	rubber -d $(DIFF_FLATTEN_TEX_FILE)

main:	clean git

git: 
	git add .
	git commit -m "$m"
	git push 

zip: paper.zip
#	zip paper.zip Makefile *.tex figures/* *.bib *.cls *.sty logo-eps-converted-to.pdf

# 1) Generate the .fls (file‐list) via pdflatex -recorder
$(FLS_FILE): $(TEX_FILE)
	@echo "Generating dependency list $(FLS_FILE)…"
	@pdflatex -interaction=nonstopmode -halt-on-error -recorder $(TEX_FILE) > /dev/null

# 2) Build paper.zip from the list of all input files (and existing .bib/.bst)
paper.zip: $(FLS_FILE)
	@echo "Collecting inputs from $(FLS_FILE)…"
	@grep '^INPUT ' $(FLS_FILE) \
		| sed 's/^INPUT //' \
		| sed 's|^\./||' \
		| while read f; do \
			if [ -f "$$f" ]; then echo "$$f"; fi; \
		  done > .deps.lst
	@echo "Adding existing .bib/.bst files…"
	@grep -h '\\bibliography' $(TEX_FILE) \
		| sed -e 's/.*{\(.*\)}/\1/' \
		| tr ',' '\n' \
		| sed 's|$$|.bib|' \
		| while read f; do \
			if [ -f "$$f" ]; then echo "$$f"; fi; \
		  done >> .deps.lst
	@grep -h '\\bibliographystyle' $(TEX_FILE) \
		| sed -e 's/.*{\(.*\)}/\1/' \
		| sed 's|$$|.bst|' \
		| while read f; do \
			if [ -f "$$f" ]; then echo "$$f"; fi; \
		  done >> .deps.lst
	@sort -u .deps.lst | zip -@ $@
	@rm .deps.lst
	@echo "Created paper.zip with all required files."

clean:  
	rm -f *.log *.synctex.gz *.aux *.bbl *.blg *.pdf figures/*converted-to.pdf
	rubber --clean -d $(BASENAME)
	rubber --clean -d $(DIFF_FLATTEN_TEX_FILE)
#rm -f $(PDF_FILE) $(BASENAME).log $(BASENAME).log $(BASENAME).aux $(BASENAME).bbl $(BASENAME).blg
