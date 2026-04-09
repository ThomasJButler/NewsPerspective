"""Seed processed articles for live local integration checks.

Run with:
    python -m src.backend.scripts.seed_manual_integration_data

The script writes deterministic processed rows into the configured database so
the Phase 3 manual frontend/backend checks have cached data before a real
NewsAPI-backed refresh is attempted.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from ..database import Base, SessionLocal, engine
from ..models import Article


@dataclass(frozen=True)
class SeedArticle:
    slug: str
    source_name: str
    source_id: str
    original_title: str
    rewritten_title: str
    tldr: str
    author: str
    category: str
    was_rewritten: bool
    original_sentiment: str
    sentiment_score: float
    is_good_news: bool
    country: str = "us"


SEED_ARTICLES: tuple[SeedArticle, ...] = (
    SeedArticle(
        slug="nhs-virtual-wards",
        source_name="BBC News",
        source_id="bbc-news",
        original_title="NHS rolls out virtual wards as hospitals face fresh pressure",
        rewritten_title="NHS expands virtual wards to ease hospital demand",
        tldr="Health services in England are widening home-based monitoring for some patients. Officials say the aim is to free beds while keeping suitable patients under clinical supervision.",
        author="Amelia Hart",
        category="health",
        was_rewritten=True,
        original_sentiment="negative",
        sentiment_score=-0.2,
        is_good_news=False,
        country="gb",
    ),
    SeedArticle(
        slug="bus-route-restoration",
        source_name="BBC News",
        source_id="bbc-news",
        original_title="Rural bus routes restored after council funding deal",
        rewritten_title="Rural bus routes return after council funding agreement",
        tldr="A local funding package will restore several rural bus services that had been cut. Councils say the change should improve access to work, school, and medical appointments.",
        author="Amelia Hart",
        category="general",
        was_rewritten=True,
        original_sentiment="positive",
        sentiment_score=0.4,
        is_good_news=True,
        country="gb",
    ),
    SeedArticle(
        slug="flood-defence-upgrade",
        source_name="BBC News",
        source_id="bbc-news",
        original_title="Town starts flood defence upgrade ahead of winter",
        rewritten_title="Town begins flood defence upgrade before winter",
        tldr="Engineers have started work on flood barriers and drainage improvements in a low-lying town. The project is intended to reduce disruption during heavy rain later in the year.",
        author="Amelia Hart",
        category="general",
        was_rewritten=False,
        original_sentiment="neutral",
        sentiment_score=0.1,
        is_good_news=False,
        country="gb",
    ),
    SeedArticle(
        slug="school-breakfast-clubs",
        source_name="BBC News",
        source_id="bbc-news",
        original_title="Breakfast club expansion reaches 200 more primary schools",
        rewritten_title="Breakfast club expansion reaches 200 more primary schools",
        tldr="More primary schools are joining a breakfast club programme aimed at supporting attendance and concentration. School leaders say demand has been strongest in lower-income areas.",
        author="Amelia Hart",
        category="education",
        was_rewritten=False,
        original_sentiment="positive",
        sentiment_score=0.6,
        is_good_news=True,
        country="gb",
    ),
    SeedArticle(
        slug="port-strike-talks",
        source_name="Reuters",
        source_id="reuters",
        original_title="Port strike talks resume as exporters seek certainty",
        rewritten_title="Port strike talks resume as exporters seek clarity",
        tldr="Union and employer representatives have resumed negotiations over pay and staffing at a major port. Exporters say a settlement would help reduce delays in the supply chain.",
        author="Jon Smith",
        category="business",
        was_rewritten=True,
        original_sentiment="negative",
        sentiment_score=-0.3,
        is_good_news=False,
    ),
    SeedArticle(
        slug="battery-plant-hiring",
        source_name="Reuters",
        source_id="reuters",
        original_title="Battery plant begins hiring for 800 manufacturing jobs",
        rewritten_title="Battery plant starts hiring for 800 manufacturing jobs",
        tldr="A battery manufacturer has opened recruitment for a new facility in northern England. The company says production is scheduled to start next year after equipment installation is complete.",
        author="Jon Smith",
        category="business",
        was_rewritten=True,
        original_sentiment="positive",
        sentiment_score=0.5,
        is_good_news=True,
    ),
    SeedArticle(
        slug="energy-grid-warning",
        source_name="Reuters",
        source_id="reuters",
        original_title="Grid operator warns of tight energy margins during cold snap",
        rewritten_title="Grid operator says energy margins may tighten during cold snap",
        tldr="The national grid operator said reserve power margins could narrow if a colder weather system arrives. It said contingency tools are available and no supply issues are currently expected.",
        author="Jon Smith",
        category="business",
        was_rewritten=True,
        original_sentiment="negative",
        sentiment_score=-0.4,
        is_good_news=False,
    ),
    SeedArticle(
        slug="solar-farm-approval",
        source_name="Reuters",
        source_id="reuters",
        original_title="UK approves solar farm planned to power 120,000 homes",
        rewritten_title="UK approves solar farm planned to supply 120,000 homes",
        tldr="A large solar project has received approval after a national planning review. Developers say construction could begin later this year if financing stays on schedule.",
        author="Jon Smith",
        category="business",
        was_rewritten=True,
        original_sentiment="positive",
        sentiment_score=0.7,
        is_good_news=True,
    ),
    SeedArticle(
        slug="rent-stability-report",
        source_name="Financial Times",
        source_id="financial-times",
        original_title="Rent growth slows across major UK cities, analysts say",
        rewritten_title="Rent growth slows across major UK cities, analysts say",
        tldr="A new market report shows rent increases moderating in several large UK cities. Analysts say supply remains tight but tenant demand has become less aggressive than last year.",
        author="Lucy Grant",
        category="business",
        was_rewritten=False,
        original_sentiment="neutral",
        sentiment_score=0.0,
        is_good_news=False,
        country="gb",
    ),
    SeedArticle(
        slug="pension-digital-service",
        source_name="Financial Times",
        source_id="financial-times",
        original_title="Pension dashboard pilot opens to more providers",
        rewritten_title="Pension dashboard pilot expands to more providers",
        tldr="More pension providers are joining a dashboard pilot designed to help savers see retirement accounts in one place. Regulators say the staged rollout is intended to reduce implementation risk.",
        author="Lucy Grant",
        category="business",
        was_rewritten=True,
        original_sentiment="positive",
        sentiment_score=0.3,
        is_good_news=True,
        country="gb",
    ),
    SeedArticle(
        slug="startup-funding-dip",
        source_name="Financial Times",
        source_id="financial-times",
        original_title="Startup funding slips as investors favour later-stage bets",
        rewritten_title="Startup funding eases as investors favour later-stage companies",
        tldr="Early-stage startup funding fell in the latest quarter as investors shifted towards larger, later-stage deals. Market observers say the slowdown is most visible in consumer apps.",
        author="Lucy Grant",
        category="technology",
        was_rewritten=True,
        original_sentiment="negative",
        sentiment_score=-0.3,
        is_good_news=False,
        country="gb",
    ),
    SeedArticle(
        slug="rail-ticket-trial",
        source_name="Financial Times",
        source_id="financial-times",
        original_title="Rail operators test simpler ticket bundles for commuters",
        rewritten_title="Rail operators test simpler ticket bundles for commuters",
        tldr="Several rail operators are trialling flexible ticket bundles aimed at part-time commuters. Industry groups say the change could reduce confusion around existing fares.",
        author="Lucy Grant",
        category="business",
        was_rewritten=False,
        original_sentiment="positive",
        sentiment_score=0.2,
        is_good_news=True,
        country="gb",
    ),
    SeedArticle(
        slug="river-cleanup-volunteers",
        source_name="The Guardian",
        source_id="the-guardian-uk",
        original_title="River cleanup campaign draws record volunteer turnout",
        rewritten_title="River cleanup campaign draws record volunteer turnout",
        tldr="Environmental groups say a weekend cleanup effort brought together a record number of local volunteers. Organisers collected waste from multiple riverbank sites and plan follow-up events.",
        author="Maya Ellis",
        category="general",
        was_rewritten=False,
        original_sentiment="positive",
        sentiment_score=0.8,
        is_good_news=True,
        country="gb",
    ),
    SeedArticle(
        slug="university-lab-funding",
        source_name="The Guardian",
        source_id="the-guardian-uk",
        original_title="University secures lab funding after months of uncertainty",
        rewritten_title="University secures funding for lab upgrade",
        tldr="A university research lab has secured funding for equipment upgrades after a delayed approval process. The institution says the changes will support work in materials science and medical testing.",
        author="Maya Ellis",
        category="science",
        was_rewritten=True,
        original_sentiment="positive",
        sentiment_score=0.4,
        is_good_news=True,
        country="gb",
    ),
    SeedArticle(
        slug="housing-target-review",
        source_name="The Guardian",
        source_id="the-guardian-uk",
        original_title="Ministers review housing target after councils raise feasibility concerns",
        rewritten_title="Ministers review housing target after councils raise feasibility concerns",
        tldr="Government ministers are reviewing housing delivery targets after local authorities raised concerns about land availability and infrastructure capacity. Officials say no final decision has been made.",
        author="Maya Ellis",
        category="general",
        was_rewritten=False,
        original_sentiment="negative",
        sentiment_score=-0.2,
        is_good_news=False,
        country="gb",
    ),
    SeedArticle(
        slug="community-clinic-opening",
        source_name="The Guardian",
        source_id="the-guardian-uk",
        original_title="Community clinic opens with same-day mental health appointments",
        rewritten_title="Community clinic opens with same-day mental health appointments",
        tldr="A new community clinic has started offering same-day mental health assessments and follow-up sessions. Local health leaders say the service is designed to reduce waiting times for early support.",
        author="Maya Ellis",
        category="health",
        was_rewritten=False,
        original_sentiment="positive",
        sentiment_score=0.7,
        is_good_news=True,
        country="gb",
    ),
    SeedArticle(
        slug="local-ai-curriculum",
        source_name="Community Wire",
        source_id="community-wire",
        original_title="Council pilots AI curriculum in adult learning centres",
        rewritten_title="Council pilots AI curriculum in adult learning centres",
        tldr="Adult learning centres in one region have started a pilot programme covering practical uses of AI tools. The courses focus on digital skills for jobseekers and small business owners.",
        author="Priya Nair",
        category="technology",
        was_rewritten=False,
        original_sentiment="positive",
        sentiment_score=0.3,
        is_good_news=True,
        country="gb",
    ),
    SeedArticle(
        slug="market-stall-grants",
        source_name="Community Wire",
        source_id="community-wire",
        original_title="Market stall grants reopen after strong first round",
        rewritten_title="Market stall grants reopen after strong first round",
        tldr="A small-business grant scheme for market traders has reopened after the first round was oversubscribed. Organisers say the next round will prioritise first-time applicants.",
        author="Priya Nair",
        category="business",
        was_rewritten=False,
        original_sentiment="positive",
        sentiment_score=0.5,
        is_good_news=True,
        country="gb",
    ),
    SeedArticle(
        slug="bridge-repair-diversion",
        source_name="Community Wire",
        source_id="community-wire",
        original_title="Bridge repair creates month-long bus diversion",
        rewritten_title="Bridge repair leads to month-long bus diversion",
        tldr="Transport officials have introduced a temporary diversion while repair work is carried out on a local bridge. The authority says the work is needed to keep the route safe for buses.",
        author="Priya Nair",
        category="general",
        was_rewritten=True,
        original_sentiment="negative",
        sentiment_score=-0.1,
        is_good_news=False,
        country="gb",
    ),
    SeedArticle(
        slug="library-late-hours",
        source_name="Community Wire",
        source_id="community-wire",
        original_title="City libraries extend evening hours during exam season",
        rewritten_title="City libraries extend evening hours during exam season",
        tldr="Libraries in the city centre and two suburbs will stay open later through the exam period. Students and parents had asked for more evening study space.",
        author="Priya Nair",
        category="education",
        was_rewritten=False,
        original_sentiment="positive",
        sentiment_score=0.4,
        is_good_news=True,
        country="gb",
    ),
    SeedArticle(
        slug="farm-water-reservoir",
        source_name="BBC News",
        source_id="bbc-news",
        original_title="Farm reservoir plan aims to cut summer water shortages",
        rewritten_title="Farm reservoir plan aims to reduce summer water shortages",
        tldr="Farm groups are backing a reservoir proposal intended to reduce seasonal water pressure. Supporters say a larger reserve could help protect food production during dry periods.",
        author="Amelia Hart",
        category="science",
        was_rewritten=True,
        original_sentiment="neutral",
        sentiment_score=0.1,
        is_good_news=False,
        country="gb",
    ),
    SeedArticle(
        slug="export-orders-rebound",
        source_name="Reuters",
        source_id="reuters",
        original_title="Mid-sized manufacturers report rebound in export orders",
        rewritten_title="Mid-sized manufacturers report rebound in export orders",
        tldr="A survey of mid-sized manufacturers found export orders improving after a weaker start to the year. Firms said demand was strongest in specialist components and industrial software.",
        author="Jon Smith",
        category="business",
        was_rewritten=False,
        original_sentiment="positive",
        sentiment_score=0.5,
        is_good_news=True,
    ),
    SeedArticle(
        slug="city-heat-pump-scheme",
        source_name="Financial Times",
        source_id="financial-times",
        original_title="Heat pump finance scheme expands to apartment blocks",
        rewritten_title="Heat pump finance scheme expands to apartment blocks",
        tldr="A green-finance programme is broadening eligibility so apartment buildings can apply for support with heat pump installations. Backers say the change could accelerate upgrades in urban housing.",
        author="Lucy Grant",
        category="business",
        was_rewritten=False,
        original_sentiment="positive",
        sentiment_score=0.4,
        is_good_news=True,
        country="gb",
    ),
    SeedArticle(
        slug="coastal-train-disruption",
        source_name="The Guardian",
        source_id="the-guardian-uk",
        original_title="Coastal train services cut after landslip risk review",
        rewritten_title="Coastal train services reduced after landslip risk review",
        tldr="Rail services on a coastal route have been reduced while engineers assess landslip risks near the track. Transport officials say safety checks will continue through the week.",
        author="Maya Ellis",
        category="general",
        was_rewritten=True,
        original_sentiment="negative",
        sentiment_score=-0.5,
        is_good_news=False,
        country="gb",
    ),
    SeedArticle(
        slug="repair-cafe-network",
        source_name="Community Wire",
        source_id="community-wire",
        original_title="Repair cafe network expands to six neighbourhood hubs",
        rewritten_title="Repair cafe network expands to six neighbourhood hubs",
        tldr="A volunteer repair network has expanded to six neighbourhood venues where residents can bring broken household items. Organisers say the project reduces waste and builds practical skills.",
        author="Priya Nair",
        category="general",
        was_rewritten=False,
        original_sentiment="positive",
        sentiment_score=0.6,
        is_good_news=True,
        country="gb",
    ),
    # ------------------------------------------------------------------
    # Cross-country story pairs for the comparison view demo.
    # Each pair is a globally-shared story covered by a UK and a US outlet
    # with overlapping headline keywords, so the comparison grouping will
    # cluster them into multi-country groups.
    # ------------------------------------------------------------------
    SeedArticle(
        slug="apple-ai-chip-us",
        source_name="Reuters",
        source_id="reuters",
        original_title="Apple reveals next-generation AI chip powering new Mac lineup",
        rewritten_title="Apple announces next-generation AI chip for new Mac lineup",
        tldr="Apple introduced a new generation of its custom silicon at a developer event, built around on-device machine learning workloads. The chip will ship first in updated Mac models later this year.",
        author="Alex Chen",
        category="technology",
        was_rewritten=True,
        original_sentiment="positive",
        sentiment_score=0.4,
        is_good_news=False,
    ),
    SeedArticle(
        slug="apple-ai-chip-uk",
        source_name="BBC News",
        source_id="bbc-news",
        original_title="Apple unveils next-generation AI chip for Mac computers",
        rewritten_title="Apple unveils next-generation AI chip for Mac computers",
        tldr="Apple has announced a new AI-focused chip for its Mac range. The company said the processor is designed for on-device machine learning and will debut in refreshed Mac models this year.",
        author="Sam Patel",
        category="technology",
        was_rewritten=False,
        original_sentiment="neutral",
        sentiment_score=0.2,
        is_good_news=False,
        country="gb",
    ),
    SeedArticle(
        slug="climate-summit-us",
        source_name="Reuters",
        source_id="reuters",
        original_title="Global leaders commit to climate action agreement at Geneva summit",
        rewritten_title="Global leaders sign climate action agreement at Geneva summit",
        tldr="Representatives from major economies signed a framework climate agreement at the Geneva summit, covering emissions targets and finance commitments. Negotiators said the deal builds on previous international pledges.",
        author="Jordan Miller",
        category="general",
        was_rewritten=True,
        original_sentiment="neutral",
        sentiment_score=0.1,
        is_good_news=False,
    ),
    SeedArticle(
        slug="climate-summit-uk",
        source_name="The Guardian",
        source_id="the-guardian-uk",
        original_title="World leaders pledge climate action at Geneva summit",
        rewritten_title="World leaders pledge climate action at Geneva summit",
        tldr="Heads of government at the Geneva climate summit signed a new framework agreement on emissions and climate finance. UK officials said the pledges represent a meaningful step on international climate cooperation.",
        author="Maya Ellis",
        category="general",
        was_rewritten=False,
        original_sentiment="positive",
        sentiment_score=0.3,
        is_good_news=False,
        country="gb",
    ),
    SeedArticle(
        slug="spacex-launch-us",
        source_name="Reuters",
        source_id="reuters",
        original_title="SpaceX launches astronauts to International Space Station in milestone mission",
        rewritten_title="SpaceX launches astronauts to International Space Station",
        tldr="SpaceX sent a new crew to the International Space Station in a routine rotation mission. The company confirmed a successful dock with the station several hours after liftoff.",
        author="Alex Chen",
        category="science",
        was_rewritten=True,
        original_sentiment="positive",
        sentiment_score=0.6,
        is_good_news=True,
    ),
    SeedArticle(
        slug="spacex-launch-uk",
        source_name="BBC News",
        source_id="bbc-news",
        original_title="SpaceX rocket launches astronauts to International Space Station",
        rewritten_title="SpaceX rocket launches astronauts to International Space Station",
        tldr="A SpaceX rocket has lifted off carrying a crew rotation for the International Space Station. The British space agency said the mission represents continued progress in international crewed flight operations.",
        author="Sam Patel",
        category="science",
        was_rewritten=False,
        original_sentiment="positive",
        sentiment_score=0.6,
        is_good_news=True,
        country="gb",
    ),
)


def upsert_seed_articles() -> tuple[int, int]:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    inserted = 0
    updated = 0
    # Seed articles are offset ~14 days into the past so that a real NewsAPI
    # refresh always produces newer articles that dominate the feed. Without
    # this offset, seed rows sort above freshly-fetched BBC/Reuters content
    # and bury the real headlines. For users running the app without an API
    # key, "2 weeks ago" is an honest representation of demo cache data.
    seed_base = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=14)

    try:
        for index, seed_article in enumerate(SEED_ARTICLES):
            published_at = seed_base - timedelta(hours=index)
            fetched_at = published_at + timedelta(minutes=15)
            url = f"https://example.com/manual-seed/{seed_article.slug}"
            article = session.query(Article).filter(Article.url == url).first()

            values = {
                "id": f"manual-seed-{index + 1:03d}",
                "original_title": seed_article.original_title,
                "rewritten_title": seed_article.rewritten_title,
                "tldr": seed_article.tldr,
                "original_description": seed_article.tldr,
                "source_name": seed_article.source_name,
                "source_id": seed_article.source_id,
                "author": seed_article.author,
                "url": url,
                "image_url": f"https://images.example.com/manual-seed/{seed_article.slug}.jpg",
                "published_at": published_at,
                "fetched_at": fetched_at,
                "was_rewritten": seed_article.was_rewritten,
                "original_sentiment": seed_article.original_sentiment,
                "sentiment_score": seed_article.sentiment_score,
                "is_good_news": seed_article.is_good_news,
                "category": seed_article.category,
                "country": seed_article.country,
                "processing_status": "processed",
            }

            if article is None:
                session.add(Article(**values))
                inserted += 1
                continue

            for field, value in values.items():
                setattr(article, field, value)
            updated += 1

        session.commit()
        return inserted, updated
    finally:
        session.close()


def main() -> None:
    inserted, updated = upsert_seed_articles()
    print(f"Seeded {len(SEED_ARTICLES)} processed articles.")
    print(f"Inserted: {inserted}")
    print(f"Updated: {updated}")


if __name__ == "__main__":
    main()
