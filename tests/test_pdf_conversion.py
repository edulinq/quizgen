import os

import quizgen.latex
import quizgen.pdf
import quizgen.util.dirent

import tests.base

MIN_PDF_SIZE_BYTES = 1000

class PdfConversionTest(tests.base.BaseTest):
    """
    Test PDF generation for quizzes in 'tests/quizzes/good' directory.
    Tests cover both local and Docker-based PDF generation.
    """

    pass

def _add_pdf_tests():
    quiz_files = tests.base.discover_good_quiz_files()
    if (not quiz_files):
        raise ValueError(f"No quiz.json files found in '{tests.base.GOOD_QUIZZES_DIR}' or its subdirectories.")

    for quiz_path in quiz_files:
        _add_pdf_test(quiz_path)

def _add_pdf_test(path):
    base_test_name = os.path.basename(os.path.dirname(path))

    # Test local PDF generation.
    test_name = f"test_quiz_pdf_local_{base_test_name}"
    setattr(PdfConversionTest, test_name, _get_quiz_pdf_local_test_method(path))

    # Test Docker PDF generation.
    test_name = f"test_quiz_pdf_docker_{base_test_name}"
    setattr(PdfConversionTest, test_name, _get_quiz_pdf_docker_test_method(path))


def _get_quiz_pdf_local_test_method(path):
    """
    Get a test for generating a PDF locally.
    """

    def __method(self):
        quizgen.latex.set_pdflatex_use_docker(False)
        if (not quizgen.latex.is_available()):
            self.skipTest("pdflatex is not available")

        _run_pdf_test(self, path)

    return __method

def _get_quiz_pdf_docker_test_method(path):
    """
    Get a test for generating a PDF with Docker.
    """

    def __method(self):
        quizgen.latex.set_pdflatex_use_docker(True)
        if (not quizgen.latex.is_available()):
            self.skipTest("Docker is not available")

        _run_pdf_test(self, path)

    return __method

def _run_pdf_test(self,path):
    temp_dir = quizgen.util.dirent.get_temp_path(prefix = "quizgen_pdf_test_")
    quiz, variants, _ = quizgen.pdf.make_with_path(path, base_out_dir = temp_dir)

    for variant in variants:
        pdf_file = os.path.join(temp_dir, quiz.title, f"{variant.title}.pdf")
        self.assertTrue(os.path.exists(pdf_file), f"PDF '{pdf_file}' not generated")
        self.assertTrue(os.path.getsize(pdf_file) > MIN_PDF_SIZE_BYTES, f"PDF '{pdf_file}' is too small")

_add_pdf_tests()