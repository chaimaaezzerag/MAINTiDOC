"""Régressions contre un vérificateur volontairement trompeur et les erreurs IO."""
import pytest
from src.grounding_rules import independent_verdict
from src.retrieval import fuse_pages

@pytest.mark.parametrize("claim,quote,verdict", [
    ("Le repère 502 désigne des écrous.", "nuts (503), screws (502), sealing (419)", "contradicted"),
    ("Le repère 419 désigne des vis.", "screws (502), sealing (419)", "contradicted"),
    ("Le repère 419 ne désigne pas un joint.", "sealing (419)", "contradicted"),
    ("Le repère 502 désigne des vis bleues.", "screws (502)", "insufficient"),
    ("Les vis 502 refroidissent le moteur.", "screws (502)", "insufficient"),
    ("Le tableau 18 concerne les couples.", "Table 17 Torques, screw (18)", "insufficient"),
    ("Le tableau 18 concerne les couples.", "Table 18 Torques BAX", "supported"),
    ("Le repère 419 correspond à un joint.", "sealing (419)", "supported"),
    ("Le joint porte le repère 419.", "sealing (419)", "supported"),
    ("Le repère 502 désigne des vis.", "screws (502), nuts (502)", "contradicted"),
    ('Le manuel indique : « Replace the sealing (419), if necessary. »', 'Replace the sealing (419), if necessary.', "supported"),
])
def test_independent_semantics(claim, quote, verdict):
    assert independent_verdict(claim, quote)[0] == verdict

def test_rrf_aligns_modalities_without_counting_duplicate_chunks():
    def link(doc): return dict(document_id=doc,page=1,element_id="page1")
    links={0:link("A"),1:link("A"),2:link("B"),-1:link("A"),-2:link("C")}
    pages, members=fuse_pages([[0,1,2],[-1,-2]],links)
    assert pages[0][0]=="A"
    assert len(pages)==3
    assert members[pages[0]]==[0,1,-1]

def test_missing_corpus_is_not_invented(monkeypatch,tmp_path):
    import src.retrieval as module
    monkeypatch.setattr(module,"DATA",tmp_path)
    with pytest.raises(FileNotFoundError): module.Retriever()

def test_checker_rejects_wrong_binding_even_when_model_says_supported():
    from src.evidence_check import check_answer
    from src.runtime_models import Reference,Evidence,Answer,EvidenceReport,ClaimCheck
    from src.ollama_client import Budget
    ref=Reference(document_id="vannes/2bax70en",page=16,element_id="page16")
    text="nuts (503), screws (502), sealing (419)"
    answer=Answer(status="answered",answer="Le repère 502 désigne des écrous.",citations=[ref],uncertainties=[])
    class WrongJudge:
        def generate(self,*args,**kwargs):
            return EvidenceReport(claims=[ClaimCheck(claim=answer.answer,verdict="supported",basis="document",citation=ref,quote=text,reason="Verdict volontairement erroné")])
    report,valid=check_answer("Que désigne 502 ?",answer,[Evidence(citation=ref,text=text)],WrongJudge(),Budget())
    assert not valid
    assert report.claims[0].verdict=="contradicted"

def test_same_citation_does_not_discard_complementary_passages():
    from src.evidence_check import check_answer
    from src.runtime_models import Reference,Evidence,Answer,EvidenceReport,ClaimCheck
    from src.ollama_client import Budget
    ref=Reference(document_id="vannes/2bax70en",page=16,element_id="page16")
    answer=Answer(status="answered",answer="Le repère 502 désigne des vis.",citations=[ref],uncertainties=[])
    class Judge:
        def generate(self,*args,**kwargs):
            return EvidenceReport(claims=[ClaimCheck(claim=answer.answer,verdict="supported",basis="document",citation=ref,quote="screws (502)",reason="Identité")])
    evidence=[Evidence(citation=ref,text="screws (502)"),Evidence(citation=ref,text="sealing (419)")]
    assert check_answer("Que désigne 502 ?",answer,evidence,Judge(),Budget())[1]
