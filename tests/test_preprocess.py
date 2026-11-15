import unittest

from ml.preprocess import clean_text, split_chunks


class CleanTextTests(unittest.TestCase):
    def test_lowercases_and_drops_urls_and_mentions(self):
        self.assertEqual(clean_text("Check https://example.com NOW @friend"), "check now")

    def test_negations_are_kept(self):
        self.assertIn("not", clean_text("I am not okay"))
        self.assertIn("no", clean_text("no good"))

    def test_punctuation_and_digits_are_removed(self):
        self.assertEqual(clean_text("I'm 100% done!!!"), "i'm done")

    def test_whitespace_collapses(self):
        self.assertEqual(clean_text("  a   b \n c "), "a b c")

    def test_empty_input(self):
        self.assertEqual(clean_text("   "), "")


class SplitChunksTests(unittest.TestCase):
    def test_short_text_is_a_single_chunk(self):
        self.assertEqual(split_chunks("i am happy"), ["i am happy"])

    def test_empty_text_yields_no_chunks(self):
        self.assertEqual(split_chunks("   "), [])
        self.assertEqual(split_chunks(""), [])

    def test_short_sentences_are_packed_together(self):
        self.assertEqual(split_chunks("a b c. d e f. g h i.", max_words=40),
                         ["a b c. d e f. g h i."])

    def test_long_text_is_split_under_the_limit(self):
        chunks = split_chunks("one two three. " * 40, max_words=20)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk.split()) <= 20 for chunk in chunks))

    def test_oversized_single_sentence_is_broken_on_whitespace(self):
        chunks = split_chunks("word " * 100, max_words=30)
        self.assertTrue(all(len(chunk.split()) <= 30 for chunk in chunks))
        self.assertEqual(sum(len(chunk.split()) for chunk in chunks), 100)

    def test_newlines_also_split_sentences(self):
        self.assertEqual(split_chunks("first part\nsecond part", max_words=1),
                         ["first", "part", "second", "part"])


if __name__ == "__main__":
    unittest.main()
