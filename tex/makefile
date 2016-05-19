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

poster.pdf: poster1.tex poster2.tex
	$(TEX) $(LATEXFLAGS) poster1.tex
	$(TEX) $(LATEXFLAGS) poster2.tex

clean-all:
	rm -f *.dvi *.log *.bak *.aux *.bbl *.blg *.idx *.ps *.eps *.pdf *.toc *.out *~

clean:
	rm -f *.log *.bak *.aux *.bbl *.blg *.idx *.toc *.out *~
