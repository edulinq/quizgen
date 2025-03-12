import os

import quizgen.latex
import quizgen.pdf
import quizgen.util.dirent

import tests.base

class PdfConversionTest(tests.base.BaseTest):
    """
    Test PDF generation for quizzes in 'tests/quizzes/good/image-questions' directory.
    A 'quiz.json' with an image question indicates a quiz that should be parsed and compiled to PDF.
    Tests covers local PDF generation, Docker PDF generation.
    """

    pass

def _add_pdf_tests():

    good_quiz_dir = os.path.join(tests.base.GOOD_QUIZZES_DIR, "image-questions")
    if (not os.path.exists(good_quiz_dir)):
        raise ValueError(f"Expected directory '{good_quiz_dir}' not found for quiz tests.")

    
    quiz_path = os.path.join(good_quiz_dir, "quiz.json")
    if (not os.path.exists(quiz_path)):
        raise ValueError(f"Expected quiz file '{quiz_path}' not found for quiz tests.")
    
    _add_pdf_test(quiz_path)

def _add_pdf_test(path):
    base_test_name = os.path.splitext(os.path.basename(os.path.dirname(path)))[0]

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

        temp_dir = quizgen.util.dirent.get_temp_path(prefix = "quizgen_pdf_test_")
        quiz, variants, _ = quizgen.pdf.make_with_path(path, base_out_dir = temp_dir)

        pdf_file = os.path.join(temp_dir, quiz.title, f"{variants[0].title}.pdf")
        self.assertTrue(os.path.exists(pdf_file), f"Local PDF '{pdf_file}' not generated")
        self.assertTrue(os.path.getsize(pdf_file) > 1000, f"Local PDF '{pdf_file}' is too small")

    return __method

def _get_quiz_pdf_docker_test_method(path):
    """
    Get a test for generating a PDF with Docker.
    """
    def __method(self):
        quizgen.latex.set_pdflatex_use_docker(True)
        if (not quizgen.latex.is_available()):
            self.skipTest("Docker is not available")

        temp_dir = quizgen.util.dirent.get_temp_path(prefix = "quizgen_pdf_test_")
        quiz, variants, _ = quizgen.pdf.make_with_path(path, base_out_dir = temp_dir)

        for variant in variants:
            pdf_file = os.path.join(temp_dir, quiz.title, f"{variant.title}.pdf")
            self.assertTrue(os.path.exists(pdf_file), f"Docker PDF '{pdf_file}' not generated")
            self.assertTrue(os.path.getsize(pdf_file) > 1000, f"Docker PDF '{pdf_file}' is too small")

    return __method

_add_pdf_tests()