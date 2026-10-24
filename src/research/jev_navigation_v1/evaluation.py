"""Inspection-budget diagnostics. Public designer controls are not empirical Jev evidence."""
from . import contracts as K


def at_budget(report, labels, budget):
    rows = {r['id']: r for r in report['inspection_queue']}
    K.need(set(labels) == set(rows), 'labels must cover every supplied record, not only selected ones')
    K.need(type(budget) is int and 0 < budget <= len(rows), 'inspection budget must be a positive bounded integer')
    for label in labels.values():
        K.need(set(label) == {'relevance', 'important', 'reason'} and label['relevance'] in ('RELEVANT', 'IRRELEVANT', 'UNRESOLVED')
               and type(label['important']) is bool and label['reason'], 'invalid separate evaluation label')
    relevant = {k for k, v in labels.items() if v['relevance'] == 'RELEVANT'}

    def score(order):
        chosen = order[:budget]
        hits = sorted(set(chosen) & relevant)
        return {'inspected': chosen, 'relevant_inspected': hits, 'precision_at_budget': len(hits) / budget,
                'recall_at_budget': len(hits) / len(relevant) if relevant else None,
                'missed_relevant': sorted(relevant - set(chosen)),
                'missed_important': sorted(k for k in relevant - set(chosen) if labels[k]['important']),
                'incorrectly_prioritised': [k for k in chosen if labels[k]['relevance'] == 'IRRELEVANT'],
                'unresolved_inspections': [k for k in chosen if labels[k]['relevance'] == 'UNRESOLVED']}
    return {'schema': 'JEV_NAVIGATION_INSPECTION_EVALUATION_V001', 'inspection_budget': budget,
            'baseline': score(report['baseline_order']), 'scripted_classification': score([r['id'] for r in report['inspection_queue']]),
            'abstentions': {r['id']: r['abstentions'] for r in rows.values() if r['abstentions']},
            'interpretation': 'Synthetic software demonstration only. Designer labels and scripted answers are separate artifacts, not independent human judgments or measured Jev effectiveness.',
            'authorises': []}
