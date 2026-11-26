"""Transparent capacity-value model. Dollar and staffing inputs are illustrative."""
from build import export
from agent import connect_data

SCENARIOS={
    'Worst':(.45,8,6,120,6),
    'Base': (.75,12,5,100,4),
    'Best': (.90,14,4,80,3),
}
RATE=45
BUILD_RATE=55
QA_RATE=50
TRAIN_HOURS=12
ANNUAL_COMPUTE=240
def calculate(half_year_count,name):
    adoption,manual,assisted,build_hours,monthly_support=SCENARIOS[name]
    volume=half_year_count*2
    cases=volume*adoption
    benefit=cases*manual/60*RATE
    review=cases*assisted/60*RATE
    startup=build_hours*BUILD_RATE+TRAIN_HOURS*RATE
    recurring_fixed=12*monthly_support*QA_RATE+ANNUAL_COMPUTE
    op=recurring_fixed+review
    contribution=benefit-op
    return dict(scenario=name,annual_volume=volume,adoption=adoption,annual_assisted_cases=cases,manual_min=manual,
        assisted_including_review_min=assisted,analyst_hourly_rate=RATE,build_hours=build_hours,build_hourly_rate=BUILD_RATE,
        training_hours=TRAIN_HOURS,initial_build_training_usd=startup,monthly_support_hours=monthly_support,support_hourly_rate=QA_RATE,
        annual_support_usd=monthly_support*12*QA_RATE,annual_compute_usd=ANNUAL_COMPUTE,annual_local_api_usd=0,
        annual_review_usd=review,annual_total_run_usd=op,annual_manual_capacity_usd=benefit,annual_net_capacity_usd=contribution,
        year1_cumulative_usd=contribution-startup,year2_cumulative_usd=2*contribution-startup,year3_cumulative_usd=3*contribution-startup,
        three_year_economic_roi=3*benefit/(startup+3*op)-1,
        payback_months=startup/contribution*12 if contribution>0 else None,
        break_even_minutes_three_year=(recurring_fixed+startup/3)*60/(cases*RATE))
def scenarios(db=None):
    if db is None:
        from contextlib import closing
        with closing(connect_data()) as connection:
            return scenarios(connection)
    n=db.execute('SELECT count(*) FROM fact_alert').fetchone()[0]
    return [calculate(n,name) for name in SCENARIOS]
if __name__=='__main__':
    rows=scenarios()
    export('cost_model.csv',rows,rows[0])
    for r in rows: print(r['scenario'],r['annual_net_capacity_usd'],r['year3_cumulative_usd'],r['payback_months'],r['break_even_minutes_three_year'])

