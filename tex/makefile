PROJECT=report
TEX=pdflatex
LATEXFLAGS+=	-file-line-error -halt-on-error -interaction nonstopmode
BIBTEX=bibtex
BUILDTEX=$(TEX) $(LATEXFLAGS) $(PROJECT).tex

all:	clean
	$(BUILDTEX)
	$(BIBTEX) $(PROJECT)
	$(BUILDTEX)
	$(BUILDTEX)
clean-all:
	rm -f *.dvi *.log *.bak *.aux *.bbl *.blg *.idx *.ps *.eps *.pdf *.toc *.out *~

clean:
	rm -f *.log *.bak *.aux *.bbl *.blg *.idx *.toc *.out *~
