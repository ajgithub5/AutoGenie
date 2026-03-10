# New Passenger Cars Market Overview

This document gives high-level context about new passenger cars in popular markets. It is used by the RAG system to ground responses.

## Segments

Passenger cars are commonly grouped into:

- Hatchbacks: compact, city-friendly, relatively affordable.
- Sedans: better rear seat comfort and boot space, often mid-range pricing.
- SUVs and crossovers: higher driving position, more space, strong demand globally.
- EVs (electric vehicles): available as hatchbacks, sedans, and SUVs, with lower running costs but higher upfront prices.

## Typical price bands (USD, approximate)

Note: actual prices vary by country, currency, and variant. These bands are for reasoning only.

- Entry hatchbacks (emerging markets): 10,000–18,000
- Compact sedans and crossovers: 20,000–30,000
- Mid-size SUVs and premium sedans: 30,000–50,000
- Entry-level luxury: 50,000–80,000

## Country-specific considerations

### United States and Canada

- Strong demand for SUVs and trucks; compact SUVs are extremely popular for families.
- Many global brands (Toyota, Honda, Hyundai, Kia, Volkswagen, BMW, Mercedes-Benz, Tesla) offer US-specific trims.
- Financing is common, with 60-month (5-year) terms frequently chosen.

### United Kingdom and European Union

- Hatchbacks and compact SUVs dominate in dense urban areas.
- Diesel powertrains are becoming less popular; petrol, hybrid, and EVs are rising.
- Incentives for EVs may be available depending on country and year.

### India

- Hatchbacks and compact SUVs dominate the new passenger car market.
- Price sensitivity is high; many purchases are below the equivalent of 20,000 USD.
- Local brands (Maruti Suzuki, Tata, Mahindra) compete with global OEMs.

## How AutoGenie should use this

- When a user gives a budget and country, map it to realistic segments.
- Suggest cars that match segment, budget, and availability.
- When unsure, explain trade-offs (for example, stretching budget slightly to move from hatchback to compact SUV).

