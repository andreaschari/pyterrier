import pandas as pd
import unittest
import pyterrier as pt

import pyterrier.transformer as ptt;

class TestOperators(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestOperators, self).__init__(*args, **kwargs)
        if not pt.started():
            pt.init()

    def test_then(self):
        def rewrite(topics):
            for index, row in topics.iterrows():
                row["query"] = row["query"] + " test"
            return topics
        fn1 = lambda topics : rewrite(topics)
        fn2 = lambda topics : rewrite(topics)
        sequence = ptt.LambdaPipeline(fn1) >> ptt.LambdaPipeline(fn2)

        self.assertTrue(isinstance(sequence, ptt.TransformerBase))
        input = pd.DataFrame([["q1", "hello"]], columns=["qid", "query"])
        output = sequence.transform(input)
        self.assertEqual(1, len(output))
        self.assertEqual("q1", output.iloc[0]["qid"])
        self.assertEqual("hello test test", output.iloc[0]["query"])

    def test_then_multi(self):
        mock1 = ptt.UniformTransformer(pd.DataFrame([["q1", "doc1", 5]], columns=["qid", "docno", "score"]))
        mock2 = ptt.UniformTransformer(pd.DataFrame([["q1", "doc1", 10]], columns=["qid", "docno", "score"]))
        mock3 = ptt.UniformTransformer(pd.DataFrame([["q1", "doc1", 10]], columns=["qid", "docno", "score"]))
        combined12 = mock1 >> mock2
        combined23 = mock2 >> mock3 
        combined123_a = combined12 >> mock3
        combined123_b = mock1 >> mock2 >> mock3
        combined123_c = mock2 >> combined23

        self.assertEqual(2, len(combined12.models))
        self.assertEqual(2, len(combined23.models))
        #self.assertEqual(3, len(combined123_a.models))
        #self.assertEqual(3, len(combined123_b.models))
        #self.assertEqual(3, len(combined123_c.models))
        self.assertEqual(2, len(combined12.models))
        self.assertEqual(2, len(combined23.models))

    def test_mul(self):
        mock = ptt.UniformTransformer(pd.DataFrame([["q1", "doc1", 5]], columns=["qid", "docno", "score"]))
        for comb in [mock * 10, 10 * mock]:
            rtr = comb.transform(None)
            self.assertEqual(1, len(rtr))
            self.assertEqual("q1", rtr.iloc[0]["qid"])
            self.assertEqual("doc1", rtr.iloc[0]["docno"])
            self.assertEqual(50, rtr.iloc[0]["score"])
    
    def test_plus(self):
        mock1 = ptt.UniformTransformer(pd.DataFrame([["q1", "doc1", 5]], columns=["qid", "docno", "score"]))
        mock2 = ptt.UniformTransformer(pd.DataFrame([["q1", "doc1", 10]], columns=["qid", "docno", "score"]))

        combined = mock1 + mock2
        # we dont need an input, as both Identity transformers will return anyway
        rtr = combined.transform(None)

        self.assertEqual(1, len(rtr))
        self.assertEqual("q1", rtr.iloc[0]["qid"])
        self.assertEqual("doc1", rtr.iloc[0]["docno"])
        self.assertEqual(15, rtr.iloc[0]["score"])

    def test_union(self):
        mock1 = ptt.UniformTransformer(pd.DataFrame([["q1", "doc1", 5]], columns=["qid", "docno", "score"]))
        mock2 = ptt.UniformTransformer(pd.DataFrame([["q1", "doc2", 10]], columns=["qid", "docno", "score"]))

        combined = mock1 | mock2
        # we dont need an input, as both Identity transformers will return anyway
        rtr = combined.transform(None)

        self.assertEqual(2, len(rtr))
        self.assertTrue("q1" in rtr["qid"].values)
        self.assertTrue("doc1" in rtr["docno"].values)
        self.assertTrue("doc2" in rtr["docno"].values)

    def test_intersect(self):
        mock1 = ptt.UniformTransformer(pd.DataFrame([["q1", "doc1", 5]], columns=["qid", "docno", "score"]))
        mock2 = ptt.UniformTransformer(pd.DataFrame([["q1", "doc2", 10], ["q1", "doc1", 10]], columns=["qid", "docno", "score"]))

        combined = mock1 & mock2
        # we dont need an input, as both Identity transformers will return anyway
        rtr = combined.transform(None)

        self.assertEqual(1, len(rtr))
        self.assertTrue("q1" in rtr["qid"].values)
        self.assertTrue("doc1" in rtr["docno"].values)
        self.assertFalse("doc2" in rtr["docno"].values)

    def test_feature_union_multi(self):
        mock1 = ptt.UniformTransformer(pd.DataFrame([["q1", "doc1", 5]], columns=["qid", "docno", "score"]))
        mock2 = ptt.UniformTransformer(pd.DataFrame([["q1", "doc1", 10]], columns=["qid", "docno", "score"]))
        mock3 = ptt.UniformTransformer(pd.DataFrame([["q1", "doc1", 15]], columns=["qid", "docno", "score"]))

        mock12a = mock1 ** mock2
        mock123a = mock1 ** mock2 ** mock3
        mock123b = mock12a ** mock3
        print(mock123b)
        
        
        self.assertEqual(2, len(mock12a.models))
        #self.assertEqual(3, len(mock123a.models))
        #self.assertEqual(3, len(mock123b.models))
        self.assertEqual(2, len(mock12a.models))

    def test_feature_union(self): 
        mock_input = ptt.UniformTransformer(pd.DataFrame([["q1", "doc1", 5]], columns=["qid", "docno", "score"]))
        
        mock_f1 = ptt.UniformTransformer(pd.DataFrame([["q1", "doc1", 10]], columns=["qid", "docno", "score"]))
        mock_f2 = ptt.UniformTransformer(pd.DataFrame([["q1", "doc1", 50]], columns=["qid", "docno", "score"]))

        # test using direct instantiation, as well as using the ** operator
        for pipeline in [mock_input >> ptt.FeatureUnionPipeline([mock_f1, mock_f2]), mock_input >> mock_f1 ** mock_f2]:

            # we dont need an input, as both Identity transformers will return anyway
            rtr = pipeline.transform(None)
            self.assertEqual(1, len(rtr))
            self.assertTrue("qid" in rtr.columns)
            self.assertTrue("docno" in rtr.columns)
            self.assertTrue("score" in rtr.columns)
            self.assertTrue("features" in rtr.columns)
            self.assertTrue("q1" in rtr["qid"].values)
            self.assertTrue("doc1" in rtr["docno"].values)
            import numpy as np
            print(rtr.iloc[0]["features"])
            self.assertTrue( np.array_equal(np.array([10,50]), rtr.iloc[0]["features"]))

if __name__ == "__main__":
    unittest.main()
        