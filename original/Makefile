.PHONY: main $(FLS_FILE) paper.zip gitadd refresh-deps project-files submission ### clean

BASENAME  = paper
TEX_FILE  = $(BASENAME).tex
PDF_FILE  = $(BASENAME).pdf
METADATA_FILES = title.txt authors.txt abstract.txt
COMMENTS_FILE = comments.txt
SUBMISSION_BASENAME = $(BASENAME)-submission
SUBMISSION_TEX_FILE = $(SUBMISSION_BASENAME).tex
SUBMISSION_PDF_FILE = $(SUBMISSION_BASENAME).pdf
PDF_TOOL=pdflatex
BIBLIO_TOOL=bibtex

ORIGINAL_FLATTEN_TEX_FILE = ../original/$(BASENAME)-flatten-v0.tex
ORIGINAL_BIB_FILE = ../original/$(BASENAME)-v0.bbl
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
PROJECT_FILES_LIST = .deps.lst
PROJECT_FILES_TMP = .deps.lst.tmp
-include $(DEPFILE)
### --------------------------------------------------------

all: $(PDF_FILE) $(SUBMISSION_PDF_FILE)

### Compilación con latexmk + generación de dependencias reales
$(PDF_FILE) $(COMMENTS_FILE) &: $(TEX_FILE) $(METADATA_FILES)
	$(LATEXMK) $(LATEXMK_OPTS) -deps -deps-out=$(DEPFILE) $(BASENAME)
	@pages=$$(pdfinfo $(PDF_FILE) | awk '/^Pages:/ { print $$2 }'); \
	figures=$$(awk '/^[[:space:]]*\\begin{figure\*?}/ { n++ } END { print n + 0 }' $(TEX_FILE)); \
	tables=$$(awk '/^[[:space:]]*\\begin{table\*?}/ { n++ } END { print n + 0 }' $(TEX_FILE)); \
	printf '%s pages, %s figures, %s tables. Submitted to be considered for publication as a Data Descriptor in the Scientific Data Journal.\n' \
	  "$$pages" "$$figures" "$$tables" > $(COMMENTS_FILE)

# Plain-text metadata accompanying the paper.
$(METADATA_FILES) &: $(TEX_FILE)
	@sed -n 's/^[[:space:]]*\\title{\(.*\)}[[:space:]]*$$/\1/p' $< > title.txt
	@sed -n 's/^[[:space:]]*\\author\(\[[^]]*\]\)\?{\(.*\)}[[:space:]]*$$/\2/p' $< \
	  | awk '{ author[++n] = $$0 } END { \
	      for (i = 1; i <= n; i++) { \
	        if (i > 1) printf (i == n ? (n == 2 ? " and " : ", and ") : ", "); \
	        printf "%s", author[i]; \
	      } \
	      if (n) printf "\n"; \
	    }' > authors.txt
	@awk ' \
	  /^[[:space:]]*\\begin{abstract}[[:space:]]*$$/ { in_abstract = 1; next } \
	  /^[[:space:]]*\\end{abstract}[[:space:]]*$$/   { \
	    if (paragraph != "") print paragraph; \
	    exit; \
	  } \
	  in_abstract { \
	    line = $$0; \
	    sub(/^[[:space:]]+/, "", line); \
	    sub(/[[:space:]]+$$/, "", line); \
	    if (line == "") { \
	      if (paragraph != "") { print paragraph; print ""; paragraph = ""; } \
	    } else { \
	      paragraph = paragraph (paragraph == "" ? "" : " ") line; \
	    } \
	  } \
	' $< \
	  | sed -e 's/\\texttt{\([^}]*\)}/\1/g' \
	        -e 's/\\,/ /g' \
	        -e 's/[$$]//g' \
	        -e 's/[[:space:]]*$$//' > abstract.txt

submission: $(SUBMISSION_PDF_FILE)

$(SUBMISSION_TEX_FILE): $(PDF_FILE) $(TEX_FILE)
	@test -f $(BASENAME).bbl || { echo "Error: $(BASENAME).bbl not found after compiling $(TEX_FILE)."; exit 2; }
	@awk ' \
	  /^[[:space:]]*\\bibliography[[:space:]]*\{$(BASENAME)\}/ { next } \
	  /^[[:space:]]*%[[:space:]]*\\input[[:space:]]*\{$(BASENAME)\.bbl\}/ { \
	    while ((getline line < "$(BASENAME).bbl") > 0) print line; \
	    close("$(BASENAME).bbl"); \
	    next; \
	  } \
	  { print } \
	' $(TEX_FILE) > $@

$(SUBMISSION_PDF_FILE): $(SUBMISSION_TEX_FILE)
	$(PDF_TOOL) $(FLAGS_SYNCTEX_PDFLATEX) $(SUBMISSION_TEX_FILE)
	$(PDF_TOOL) $(FLAGS_SYNCTEX_PDFLATEX) $(SUBMISSION_TEX_FILE)

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

# Regenera una sola vez el fichero de dependencias para zip y gitadd.
refresh-deps: $(TEX_FILE)
	@echo "Refreshing LaTeX dependencies..."
	@$(LATEXMK) $(LATEXMK_OPTS) -deps -deps-out=$(DEPFILE) $(BASENAME)

# Extrae una única lista compartida de ficheros locales necesarios para compilar.
project-files: refresh-deps
	@echo "Collecting inputs from $(DEPFILE)..."
	@sed -e ':a' -e 'N' -e 's/\\\n/ /' -e 'ta' $(DEPFILE) \
	  | sed 's/^[^:]*:[[:space:]]*//' \
	  | tr ' ' '\n' \
	  | sed 's|^\./||' \
	  | grep -v '^[[:space:]]*$$' \
	  | grep -v '^/' \
	  | grep -v '^\.\./' \
	  | sort -u > $(PROJECT_FILES_TMP)
	@while IFS= read -r f; do \
	    [ -f "$$f" ] && printf '%s\n' "$$f"; \
	  done < $(PROJECT_FILES_TMP) > $(PROJECT_FILES_LIST)
	@test -s $(PROJECT_FILES_LIST) || { \
	  echo "No project-local inputs found in $(DEPFILE)."; \
	  rm -f $(PROJECT_FILES_TMP) $(PROJECT_FILES_LIST); \
	  exit 12; \
	}
	@printf '%s\n' Makefile >> $(PROJECT_FILES_LIST)
	@sort -u -o $(PROJECT_FILES_LIST) $(PROJECT_FILES_LIST)
	@rm -f $(PROJECT_FILES_TMP)

# Build paper.zip from the shared project-file list.
paper.zip: project-files
	@zip -@ $@ < $(PROJECT_FILES_LIST)
	@echo "Created $@ with project files only."


gitadd: project-files
	@command -v git >/dev/null 2>&1 || { echo "Error: git is not installed."; exit 2; }
	@git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "Error: not inside a Git repository."; exit 2; }
	@set -e; while IFS= read -r f; do \
	    echo "git add -- $$f"; \
	    git add -- "$$f"; \
	  done < $(PROJECT_FILES_LIST)
	@echo "All project-local compilation dependencies have been added to Git."

### Limpieza sin rubber: usa latexmk -C y borra artefactos auxiliares
clean:
	$(LATEXMK) -C $(BASENAME)
	rm -f $(DEPFILE) paper.zip $(PROJECT_FILES_LIST) $(PROJECT_FILES_TMP) paper.bbl *.out \
	      $(METADATA_FILES) $(COMMENTS_FILE) \
	      $(SUBMISSION_TEX_FILE) $(SUBMISSION_PDF_FILE) $(SUBMISSION_BASENAME).aux \
	      $(SUBMISSION_BASENAME).log $(SUBMISSION_BASENAME).out \
	      $(DIFF_FLATTEN_BASENAME).aux $(DIFF_FLATTEN_BASENAME).bbl \
	      $(DIFF_FLATTEN_BASENAME).blg $(DIFF_FLATTEN_BASENAME).log \
	      figures/*converted-to.pdf

.PHONY: zip-distrib

# Build a self-contained archive for compiling the generated submission source.
zip-distrib: submission project-files Makefile.distrib
	@rm -rf .zip-distrib
	@mkdir -p .zip-distrib
	@set -e; while IFS= read -r f; do \
	  case "$$f" in Makefile|paper.tex|paper.bib|IEEEtran-nonote.bst) continue;; esac; \
	  mkdir -p ".zip-distrib/$$(dirname "$$f")"; \
	  cp "$$f" ".zip-distrib/$$f"; \
	done < $(PROJECT_FILES_LIST)
	@cp $(SUBMISSION_TEX_FILE) .zip-distrib/
	@cp Makefile.distrib .zip-distrib/Makefile
	@rm -f $(SUBMISSION_BASENAME).zip
	@cd .zip-distrib && zip -q -r ../$(SUBMISSION_BASENAME).zip .
	@rm -rf .zip-distrib
	@echo "Created $(SUBMISSION_BASENAME).zip; unpack it and run 'make'."
