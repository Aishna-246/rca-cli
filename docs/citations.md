# Academic Citations

This project draws on the following published research for its demo scenarios,
benchmark validation, and stated MTTR improvement statistics.

---

## 1. RCAEval — Root Cause Analysis Benchmark

**Paper:**  
Pham, L., Ha, H., & Zhang, H. (2024). Root Cause Analysis for Microservice
System based on Causal Inference: How Far Are We? *Proceedings of the 39th
IEEE/ACM International Conference on Automated Software Engineering (ASE 2024)*,
pp. 706–715.

**arXiv:** https://arxiv.org/abs/2305.15374  
**DOI:** https://dl.acm.org/doi/abs/10.1145/3691620.3695065  
**Code:** https://github.com/phamquiluan/RCAEval  
**Dataset:** https://figshare.com/articles/dataset/RCAEval_A_Benchmark_for_Root_Cause_Analysis_of_Microservice_Systems/31048672

**BibTeX:**
```bibtex
@inproceedings{pham2024root,
  title={Root Cause Analysis for Microservice System based on Causal Inference: How Far Are We?},
  author={Pham, Luan and Ha, Huong and Zhang, Hongyu},
  booktitle={Proceedings of the 39th IEEE/ACM International Conference on Automated Software Engineering},
  pages={706--715},
  year={2024}
}
```

**Relevance:** The `examples/re2_real_failure/` demo scenarios are drawn from
the RE2-OB dataset in this benchmark (735 real failure cases, 9 datasets, 11 fault
types across Online Boutique, Sock Shop, and Train Ticket microservice systems).

---

## 2. Loghub — Large-Scale Log Dataset

**Paper:**  
Xu, W., Huang, L., Fox, A., Patterson, D., & Jordan, M. I. (2009). Detecting
Large-Scale System Problems by Mining Console Logs. *Proceedings of the ACM
Symposium on Operating Systems Principles (SOSP 2009)*.

**URL:** https://github.com/logpai/loghub  
**Dataset:** https://zenodo.org/record/3227177

**BibTeX:**
```bibtex
@inproceedings{xu2009detecting,
  title={Detecting Large-Scale System Problems by Mining Console Logs},
  author={Xu, Wei and Huang, Ling and Fox, Armando and Patterson, David and Jordan, Michael I.},
  booktitle={Proceedings of the ACM Symposium on Operating Systems Principles (SOSP)},
  year={2009}
}
```

**Relevance:** The `examples/hdfs_failure/` demo scenario is based on HDFS failure
patterns documented in the Loghub dataset (datanode disk failure → NameNode Safe
Mode → write unavailability cascade).

---

## 3. RCA Research Gap — Microservice Survey

**Paper:**  
arXiv:2408.00803 — "A Survey on Root Cause Analysis of Microservice Systems"
(2024).

**arXiv:** https://arxiv.org/abs/2408.00803

**BibTeX:**
```bibtex
@article{survey2024rca,
  title={A Survey on Root Cause Analysis of Microservice Systems},
  journal={arXiv preprint arXiv:2408.00803},
  year={2024}
}
```

**Relevance:** Cited to support the framing of the RCA problem space —
the gap between manual correlation of multi-source telemetry and automated
causal inference approaches.

---

## 4. MTTR Reduction Statistic

**Source:**  
"AI-Driven Log Analysis Reduces Mean Time to Repair from 47 Minutes to 8 Minutes."
*International Journal of Engineering and Technical Computing Science and Information
Technology (IJETCSIT)*, December 2024.

**Relevance:** The 47-minute average MTTR figure cited in README.md and the
project description comes from this industry study. The 8-minute figure with
AI-assisted log analysis is the motivating benchmark for RCA-CLI's design goal
of returning a root cause in under 30 seconds.
