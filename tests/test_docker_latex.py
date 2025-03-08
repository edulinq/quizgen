import os
import shutil
import unittest
import logging

import quizgen.latex
import quizgen.pdf
import quizgen.util.dirent
import quizgen.util.json
import tests.base

class TestDockerPdfConversion(tests.base.BaseTest):
    def test_quiz_to_pdf(self):
        if not quizgen.latex.is_available(use_docker = True):
            self.skipTest("Docker is not installed or not running")

        source_quiz_path = tests.base.discover_good_quiz_files()[0]

        if not os.path.exists(source_quiz_path):
            self.skipTest(f"Quiz file '{source_quiz_path}' not found")

        temp_dir = quizgen.util.dirent.get_temp_path()
        quiz_json_path = os.path.join(temp_dir, "quiz.json")

        quizgen.util.dirent.copy_dirent(source_quiz_path, quiz_json_path)

        original_base_dir = os.path.dirname(source_quiz_path)
        quiz_data = quizgen.util.json.load_path(quiz_json_path)
        
        for group in quiz_data["groups"]:
            for i, question_path in enumerate(group["questions"]):
                if not os.path.isabs(question_path):
                    group["questions"][i] = os.path.normpath(os.path.join(original_base_dir, question_path))

        quizgen.util.json.dump_path(quiz_data, quiz_json_path)  
        quiz_title = quiz_data.get("title", "Single Question Quiz")
        quizgen.latex.set_pdflatex_use_docker(True)
        quizgen.pdf.make_with_path(quiz_json_path, base_out_dir = temp_dir)

        pdf_file = os.path.join(temp_dir, quiz_title, f"{quiz_title}.pdf")
        assert os.path.exists(pdf_file), f"PDF file '{pdf_file}' not generated"
        assert os.path.getsize(pdf_file) > 1000, f"Generated PDF '{pdf_file}' is too small"
        
        quizgen.util.dirent.remove_dirent(temp_dir)
