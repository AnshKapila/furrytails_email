# Schema Templates

Ready-to-customize JSON-LD templates for every Google-supported structured data type. Copy the template, replace placeholder values with the user's actual content, wrap in `<script type="application/ld+json">...</script>`, and paste into the page's `<head>`.

Each template lists **required** fields Google needs for rich results and **recommended** fields that noticeably improve the rich result.

## Table of contents

1. [Article (News / Blog)](#1-article--newsarticle--blogposting)
2. [BreadcrumbList](#2-breadcrumblist)
3. [Carousel (ItemList)](#3-carousel-itemlist)
4. [Course](#4-course)
5. [Dataset](#5-dataset)
6. [DiscussionForumPosting](#6-discussionforumposting)
7. [Quiz (Education Q&A)](#7-quiz-education-qa)
8. [EmployerAggregateRating](#8-employeraggregaterating)
9. [Event](#9-event)
10. [FAQPage](#10-faqpage)
11. [ImageObject](#11-imageobject)
12. [JobPosting](#12-jobposting)
13. [LocalBusiness](#13-localbusiness)
14. [MathSolver](#14-mathsolver)
15. [Movie](#15-movie)
16. [Organization](#16-organization)
17. [Product (Snippet + Merchant Listing)](#17-product)
18. [ProfilePage](#18-profilepage)
19. [QAPage](#19-qapage)
20. [Recipe](#20-recipe)
21. [Review / AggregateRating](#21-review--aggregaterating)
22. [SoftwareApplication](#22-softwareapplication)
23. [Speakable](#23-speakable)
24. [Subscription / Paywalled Content](#24-subscription--paywalled-content)
25. [VacationRental](#25-vacationrental)
26. [VideoObject](#26-videoobject)
27. [WebSite (+ SearchAction)](#27-website-with-searchaction)

---

## How to use these templates

1. Copy the relevant block.
2. Replace every `"..."` or placeholder with the user's real data. Leave a field out rather than faking it.
3. Wrap the final JSON in `<script type="application/ld+json">` tags.
4. Paste into the `<head>` of the HTML page.
5. Validate with https://search.google.com/test/rich-results.

**Multiple schemas on one page:** use multiple `<script>` blocks, or use a JSON-LD `@graph` array. Both work; separate scripts are easier to maintain.

---

## 1. Article / NewsArticle / BlogPosting

**Required:** `headline`, `image`, `datePublished`, `author`
**Recommended:** `dateModified`, `publisher` (with logo), `description`, `mainEntityOfPage`

```json
{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "Title of the Article (≤110 chars)",
  "image": [
    "https://example.com/photos/1x1/photo.jpg",
    "https://example.com/photos/4x3/photo.jpg",
    "https://example.com/photos/16x9/photo.jpg"
  ],
  "datePublished": "2024-01-05T08:00:00+08:00",
  "dateModified": "2024-02-05T09:20:00+08:00",
  "description": "Short summary of the article.",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://example.com/article-url"
  },
  "author": [{
    "@type": "Person",
    "name": "Jane Doe",
    "url": "https://example.com/profile/janedoe"
  }],
  "publisher": {
    "@type": "Organization",
    "name": "Example Publisher",
    "logo": {
      "@type": "ImageObject",
      "url": "https://example.com/logo.png"
    }
  }
}
```

Swap `"@type": "NewsArticle"` for `"Article"` or `"BlogPosting"` as appropriate. Multi-author: make `author` an array of `Person` objects.

---

## 2. BreadcrumbList

**Required:** `itemListElement` array with `position`, `name`, and `item` (except the last item, where `item` is optional).

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Books", "item": "https://example.com/books" },
    { "@type": "ListItem", "position": 2, "name": "Science Fiction", "item": "https://example.com/books/sciencefiction" },
    { "@type": "ListItem", "position": 3, "name": "Award Winners" }
  ]
}
```

For pages reachable via multiple paths, emit multiple BreadcrumbList objects as separate scripts or an array.

---

## 3. Carousel (ItemList)

Use ItemList to wrap any set of like items (recipes, courses, movies, products, events). Combine with the specific type — ItemList alone won't produce a carousel.

**Summary pattern** — each list item points to a detail page:

```json
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "url": "https://example.com/item-1" },
    { "@type": "ListItem", "position": 2, "url": "https://example.com/item-2" },
    { "@type": "ListItem", "position": 3, "url": "https://example.com/item-3" }
  ]
}
```

**All-in-one pattern** — each list item embeds the full object:

```json
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "item": {
        "@type": "Movie",
        "url": "https://example.com/movies#a-star-is-born",
        "name": "A Star Is Born",
        "image": "https://example.com/photos/poster.jpg",
        "dateCreated": "2018-10-05",
        "director": { "@type": "Person", "name": "Bradley Cooper" },
        "aggregateRating": { "@type": "AggregateRating", "ratingValue": 90, "bestRating": 100, "ratingCount": 19141 }
      }
    }
  ]
}
```

Swap `Movie` for `Recipe`, `Course`, `Restaurant`, or `Product` to adapt.

---

## 4. Course

**Required:** `name`, `description`, `provider`
**For rich results:** add `hasCourseInstance` with at least one `CourseInstance`.

```json
{
  "@context": "https://schema.org",
  "@type": "Course",
  "name": "Introduction to Computer Science",
  "description": "An introductory CS course laying out the basics of programming.",
  "provider": {
    "@type": "Organization",
    "name": "Example University",
    "sameAs": "https://www.example.edu"
  },
  "hasCourseInstance": [{
    "@type": "CourseInstance",
    "courseMode": "Online",
    "courseWorkload": "PT40H",
    "instructor": { "@type": "Person", "name": "Dr. Jane Doe" }
  }],
  "offers": {
    "@type": "Offer",
    "price": 499,
    "priceCurrency": "USD"
  }
}
```

---

## 5. Dataset

**Required:** `name`, `description`
**Recommended:** `url`, `license`, `creator`, `distribution`, `temporalCoverage`, `spatialCoverage`, `keywords`

```json
{
  "@context": "https://schema.org/",
  "@type": "Dataset",
  "name": "NCDC Storm Events Database",
  "description": "Storm Data provided by the National Weather Service containing storm statistics from 1950 onward.",
  "url": "https://example.com/dataset",
  "keywords": ["CYCLONES", "DROUGHT", "FOG", "FREEZE"],
  "license": "https://creativecommons.org/publicdomain/zero/1.0/",
  "isAccessibleForFree": true,
  "creator": {
    "@type": "Organization",
    "url": "https://www.ncei.noaa.gov/",
    "name": "NCEI, NOAA"
  },
  "distribution": [
    { "@type": "DataDownload", "encodingFormat": "CSV", "contentUrl": "https://example.com/data.csv" },
    { "@type": "DataDownload", "encodingFormat": "XML", "contentUrl": "https://example.com/data.xml" }
  ],
  "temporalCoverage": "1950-01-01/2024-12-31"
}
```

---

## 6. DiscussionForumPosting

**Required:** `headline` or `text`, `author`, `datePublished`

```json
{
  "@context": "https://schema.org",
  "@type": "DiscussionForumPosting",
  "mainEntityOfPage": "https://example.com/post/thread-123",
  "headline": "I went to the concert last night!",
  "text": "Full text of the original post...",
  "url": "https://example.com/post/thread-123",
  "author": {
    "@type": "Person",
    "name": "Katie Pope",
    "url": "https://example.com/user/katie-pope"
  },
  "datePublished": "2024-03-01T08:34:34+02:00",
  "interactionStatistic": [{
    "@type": "InteractionCounter",
    "interactionType": "https://schema.org/LikeAction",
    "userInteractionCount": 27
  }],
  "comment": [
    {
      "@type": "Comment",
      "text": "Who were you with?",
      "author": { "@type": "Person", "name": "Saul Douglas" },
      "datePublished": "2024-03-01T09:46:02+02:00"
    },
    {
      "@type": "Comment",
      "text": "That's my mom — isn't she cool?",
      "author": { "@type": "Person", "name": "Katie Pope" },
      "datePublished": "2024-03-01T09:50:25+02:00"
    }
  ]
}
```

---

## 7. Quiz (Education Q&A)

**Required:** `hasPart` array of `Question` entries, each with `acceptedAnswer`.

```json
{
  "@context": "https://schema.org",
  "@type": "Quiz",
  "name": "Biology Flashcards",
  "hasPart": [
    {
      "@type": "Question",
      "eduQuestionType": "Flashcard",
      "text": "What is the largest organ in the human body?",
      "acceptedAnswer": { "@type": "Answer", "text": "The skin" }
    },
    {
      "@type": "Question",
      "eduQuestionType": "Flashcard",
      "text": "What is the powerhouse of the cell?",
      "acceptedAnswer": { "@type": "Answer", "text": "The mitochondria" }
    }
  ]
}
```

---

## 8. EmployerAggregateRating

**Required:** `itemReviewed` (Organization), `ratingValue`, `ratingCount`

```json
{
  "@context": "https://schema.org/",
  "@type": "EmployerAggregateRating",
  "itemReviewed": {
    "@type": "Organization",
    "name": "Example Inc.",
    "sameAs": "https://example.com"
  },
  "ratingValue": 91,
  "bestRating": 100,
  "worstRating": 1,
  "ratingCount": 10561
}
```

---

## 9. Event

**Required:** `name`, `startDate`, `location`
**Recommended:** `endDate`, `eventAttendanceMode`, `eventStatus`, `image`, `description`, `offers`, `performer`, `organizer`

```json
{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": "The Adventures of Kira and Morrison",
  "startDate": "2025-07-21T19:00-05:00",
  "endDate": "2025-07-21T23:00-05:00",
  "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
  "eventStatus": "https://schema.org/EventScheduled",
  "location": {
    "@type": "Place",
    "name": "Snickerpark Stadium",
    "address": {
      "@type": "PostalAddress",
      "streetAddress": "100 West Snickerpark Dr",
      "addressLocality": "Snickertown",
      "postalCode": "19019",
      "addressRegion": "PA",
      "addressCountry": "US"
    }
  },
  "image": ["https://example.com/event.jpg"],
  "description": "Kira and Morrison live in Snickertown!",
  "offers": {
    "@type": "Offer",
    "url": "https://example.com/tickets",
    "price": 30,
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock",
    "validFrom": "2024-01-20T16:20-08:00"
  },
  "performer": { "@type": "PerformingGroup", "name": "Kira and Morrison" },
  "organizer": { "@type": "Organization", "name": "Kira and Morrison Music", "url": "https://example.com" }
}
```

For online events, replace `location` with:
```json
"location": { "@type": "VirtualLocation", "url": "https://example.com/livestream" }
```

---

## 10. FAQPage

⚠️ **Rich result gated to government and authoritative health sites.** Markup is still valid elsewhere; rich results won't appear.

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is the return policy?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Most unopened items in new condition can be returned within 30 days."
      }
    },
    {
      "@type": "Question",
      "name": "How long does shipping take?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Standard shipping takes 3-5 business days."
      }
    }
  ]
}
```

---

## 11. ImageObject

**For image metadata rich features:** `contentUrl`, `creator`, `creditText`, `copyrightNotice`, `license`, `acquireLicensePage`.

```json
{
  "@context": "https://schema.org/",
  "@type": "ImageObject",
  "contentUrl": "https://example.com/photos/cat.jpg",
  "license": "https://www.example.com/license",
  "acquireLicensePage": "https://www.example.com/how-to-license",
  "creditText": "Jane Doe Photography",
  "creator": { "@type": "Person", "name": "Jane Doe" },
  "copyrightNotice": "© Jane Doe 2024"
}
```

---

## 12. JobPosting

**Required:** `title`, `description`, `datePosted`, `hiringOrganization`, `jobLocation` (or remote fields)
**Recommended:** `validThrough`, `employmentType`, `baseSalary`, `identifier`

```json
{
  "@context": "https://schema.org/",
  "@type": "JobPosting",
  "title": "Software Engineer",
  "description": "<p>We're looking for a software engineer to join our backend team...</p>",
  "identifier": {
    "@type": "PropertyValue",
    "name": "Example Corp",
    "value": "1234567"
  },
  "datePosted": "2024-01-18",
  "validThrough": "2024-03-18T00:00",
  "employmentType": "FULL_TIME",
  "hiringOrganization": {
    "@type": "Organization",
    "name": "Example Corp",
    "sameAs": "https://www.example.com",
    "logo": "https://www.example.com/logo.png"
  },
  "jobLocation": {
    "@type": "Place",
    "address": {
      "@type": "PostalAddress",
      "streetAddress": "1600 Amphitheatre Pkwy",
      "addressLocality": "Mountain View",
      "addressRegion": "CA",
      "postalCode": "94043",
      "addressCountry": "US"
    }
  },
  "baseSalary": {
    "@type": "MonetaryAmount",
    "currency": "USD",
    "value": {
      "@type": "QuantitativeValue",
      "value": 120000,
      "unitText": "YEAR"
    }
  }
}
```

**For remote jobs, add:**
```json
"jobLocationType": "TELECOMMUTE",
"applicantLocationRequirements": { "@type": "Country", "name": "USA" }
```

---

## 13. LocalBusiness

**Required:** `name`, `address`
**Recommended:** `image`, `telephone`, `openingHoursSpecification`, `geo`, `url`, `priceRange`

Use a specific subtype where possible: `Restaurant`, `Store`, `Plumber`, `Dentist`, `MedicalClinic`, `LegalService`, `HairSalon`, `Hotel`, `AutoRepair`, etc.

```json
{
  "@context": "https://schema.org",
  "@type": "Restaurant",
  "name": "Dave's Steak House",
  "image": "https://example.com/photos/restaurant.jpg",
  "url": "https://example.com",
  "telephone": "+15551234567",
  "priceRange": "$$",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "148 W 51st St",
    "addressLocality": "New York",
    "addressRegion": "NY",
    "postalCode": "10019",
    "addressCountry": "US"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 40.761293,
    "longitude": -73.982294
  },
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "opens": "11:30",
      "closes": "22:00"
    },
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Saturday", "Sunday"],
      "opens": "16:00",
      "closes": "23:00"
    }
  ],
  "servesCuisine": "American",
  "acceptsReservations": true
}
```

**Multi-type business** (e.g., electrician who also does plumbing):
```json
"@type": ["Electrician", "Plumber"]
```

---

## 14. MathSolver

```json
{
  "@context": "https://schema.org",
  "@type": "MathSolver",
  "name": "Example Math Solver",
  "url": "https://www.example.com/solver",
  "usageInfo": "https://www.example.com/privacy",
  "potentialAction": [{
    "@type": "SolveMathAction",
    "target": "https://www.example.com/solve?q={math_expression_string}",
    "mathExpression-input": "required name=math_expression_string",
    "eduQuestionType": ["Polynomial", "Arithmetic", "Algebra"]
  }]
}
```

---

## 15. Movie

**Required (for Movie rich result):** `name`, `image`, `dateCreated`, `director`

```json
{
  "@context": "https://schema.org",
  "@type": "Movie",
  "name": "A Star Is Born",
  "image": "https://example.com/photos/poster.jpg",
  "dateCreated": "2018-10-05",
  "director": { "@type": "Person", "name": "Bradley Cooper" },
  "actor": [
    { "@type": "Person", "name": "Lady Gaga" },
    { "@type": "Person", "name": "Bradley Cooper" }
  ],
  "review": {
    "@type": "Review",
    "reviewRating": { "@type": "Rating", "ratingValue": 5 },
    "author": { "@type": "Person", "name": "John D." }
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": 90,
    "bestRating": 100,
    "ratingCount": 19141
  }
}
```

---

## 16. Organization

**Required (for Knowledge Panel / entity recognition):** `name`, `url`
**Highly recommended:** `logo`, `sameAs`, `contactPoint`, `description`

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Example Inc.",
  "alternateName": "Example",
  "url": "https://www.example.com",
  "logo": "https://www.example.com/images/logo.png",
  "description": "We do example things since 2010.",
  "foundingDate": "2010-03-15",
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+1-555-555-5555",
    "contactType": "customer service",
    "availableLanguage": ["English", "Spanish"]
  },
  "sameAs": [
    "https://www.facebook.com/example",
    "https://www.twitter.com/example",
    "https://www.linkedin.com/company/example",
    "https://en.wikipedia.org/wiki/Example_Inc"
  ]
}
```

**Subtypes to prefer when applicable:** `OnlineStore`, `NewsMediaOrganization`, `NGO`, `GovernmentOrganization`, `EducationalOrganization`, `MedicalOrganization`.

---

## 17. Product

### Product Snippet (editorial / not selling)

**Required:** `name`, and one of `review` / `aggregateRating` / `offers`

```json
{
  "@context": "https://schema.org/",
  "@type": "Product",
  "name": "Executive Anvil",
  "image": "https://example.com/photos/anvil.jpg",
  "description": "A sleek anvil for the traveling professional.",
  "brand": { "@type": "Brand", "name": "ACME" },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": 4.4,
    "reviewCount": 89
  },
  "review": [{
    "@type": "Review",
    "author": { "@type": "Person", "name": "Fred Benson" },
    "reviewRating": { "@type": "Rating", "ratingValue": 4, "bestRating": 5 }
  }]
}
```

### Merchant Listing (selling on this page)

**Required:** `name`, `image`, `offers` with `price`, `priceCurrency`, `availability`, `itemCondition`
**Strongly recommended:** `sku` or `gtin`/`mpn`, `shippingDetails`, `hasMerchantReturnPolicy`

```json
{
  "@context": "https://schema.org/",
  "@type": "Product",
  "name": "Executive Anvil",
  "image": ["https://example.com/photos/1x1.jpg", "https://example.com/photos/16x9.jpg"],
  "description": "A sleek anvil, perfect for the business traveler.",
  "sku": "0446310786",
  "gtin14": "00012345678905",
  "brand": { "@type": "Brand", "name": "ACME" },
  "offers": {
    "@type": "Offer",
    "url": "https://example.com/anvil",
    "priceCurrency": "USD",
    "price": 119.99,
    "priceValidUntil": "2024-12-31",
    "availability": "https://schema.org/InStock",
    "itemCondition": "https://schema.org/NewCondition",
    "hasMerchantReturnPolicy": {
      "@type": "MerchantReturnPolicy",
      "applicableCountry": "US",
      "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
      "merchantReturnDays": 30,
      "returnMethod": "https://schema.org/ReturnByMail",
      "returnFees": "https://schema.org/FreeReturn"
    },
    "shippingDetails": {
      "@type": "OfferShippingDetails",
      "shippingRate": {
        "@type": "MonetaryAmount",
        "value": 5.99,
        "currency": "USD"
      },
      "shippingDestination": {
        "@type": "DefinedRegion",
        "addressCountry": "US"
      },
      "deliveryTime": {
        "@type": "ShippingDeliveryTime",
        "handlingTime": { "@type": "QuantitativeValue", "minValue": 0, "maxValue": 1, "unitCode": "DAY" },
        "transitTime": { "@type": "QuantitativeValue", "minValue": 1, "maxValue": 5, "unitCode": "DAY" }
      }
    }
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": 4.4,
    "reviewCount": 89
  }
}
```

**Multiple variants** — use `offers` as an array:
```json
"offers": [
  { "@type": "Offer", "name": "Small", "price": 79.99, "priceCurrency": "USD", "availability": "https://schema.org/InStock", "url": "https://example.com/anvil-small" },
  { "@type": "Offer", "name": "Large", "price": 119.99, "priceCurrency": "USD", "availability": "https://schema.org/InStock", "url": "https://example.com/anvil-large" }
]
```

---

## 18. ProfilePage

```json
{
  "@context": "https://schema.org",
  "@type": "ProfilePage",
  "dateCreated": "2019-08-30T15:22:46-07:00",
  "dateModified": "2024-01-15T10:00:00-07:00",
  "mainEntity": {
    "@type": "Person",
    "name": "Jane Doe",
    "alternateName": "janedoe",
    "identifier": "123475",
    "description": "Software engineer who loves cats and Kubernetes.",
    "image": "https://example.com/janedoe.jpg",
    "sameAs": [
      "https://www.twitter.com/janedoe",
      "https://www.github.com/janedoe",
      "https://www.linkedin.com/in/janedoe"
    ],
    "interactionStatistic": [
      {
        "@type": "InteractionCounter",
        "interactionType": "https://schema.org/FollowAction",
        "userInteractionCount": 5000
      },
      {
        "@type": "InteractionCounter",
        "interactionType": "https://schema.org/LikeAction",
        "userInteractionCount": 3000
      }
    ]
  }
}
```

---

## 19. QAPage

```json
{
  "@context": "https://schema.org",
  "@type": "QAPage",
  "mainEntity": {
    "@type": "Question",
    "name": "How many ounces are in a pound?",
    "text": "I'm trying to convert a recipe from grams and want to know the conversion.",
    "answerCount": 2,
    "upvoteCount": 26,
    "dateCreated": "2024-07-23T21:11Z",
    "author": { "@type": "Person", "name": "John Doe" },
    "acceptedAnswer": {
      "@type": "Answer",
      "text": "1 pound = 16 ounces.",
      "dateCreated": "2024-07-24T21:11Z",
      "upvoteCount": 1337,
      "author": { "@type": "Person", "name": "Jane Smith" }
    },
    "suggestedAnswer": [{
      "@type": "Answer",
      "text": "There are approximately 16 ounces in a pound.",
      "dateCreated": "2024-07-25T21:11Z",
      "upvoteCount": 42,
      "author": { "@type": "Person", "name": "Bob Jones" }
    }]
  }
}
```

---

## 20. Recipe

**Required:** `name`, `image`, `recipeIngredient`, `recipeInstructions`
**Strongly recommended:** `author`, `datePublished`, `description`, `prepTime`, `cookTime`, `totalTime`, `recipeYield`, `aggregateRating`, `nutrition`

```json
{
  "@context": "https://schema.org/",
  "@type": "Recipe",
  "name": "Peanut Butter Cookies",
  "image": [
    "https://example.com/photos/1x1/photo.jpg",
    "https://example.com/photos/4x3/photo.jpg",
    "https://example.com/photos/16x9/photo.jpg"
  ],
  "author": { "@type": "Person", "name": "Wendy Darling" },
  "datePublished": "2024-03-10",
  "description": "The best peanut butter cookies with a crisp outside and chewy center.",
  "prepTime": "PT10M",
  "cookTime": "PT25M",
  "totalTime": "PT35M",
  "recipeCuisine": "American",
  "recipeCategory": "Dessert",
  "keywords": "peanut butter, cookies, dessert",
  "recipeYield": "24 cookies",
  "nutrition": {
    "@type": "NutritionInformation",
    "calories": "120 calories"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": 4.8,
    "ratingCount": 18
  },
  "recipeIngredient": [
    "2 cups peanut butter",
    "1/3 cup sugar",
    "2 large eggs"
  ],
  "recipeInstructions": [
    { "@type": "HowToStep", "text": "Mix peanut butter and sugar." },
    { "@type": "HowToStep", "text": "Roll dough into balls and place on a cookie sheet." },
    { "@type": "HowToStep", "text": "Bake at 350°F for 25 minutes." }
  ],
  "video": {
    "@type": "VideoObject",
    "name": "How to make peanut butter cookies",
    "description": "Video walk-through of the peanut butter cookie recipe.",
    "thumbnailUrl": "https://example.com/photos/video-thumb.jpg",
    "uploadDate": "2024-03-10",
    "contentUrl": "https://example.com/video.mp4"
  }
}
```

---

## 21. Review / AggregateRating

These are almost always embedded inside another type (Product, Movie, Book, LocalBusiness). Standalone Review rich results no longer exist.

```json
{
  "@context": "https://schema.org/",
  "@type": "Product",
  "name": "AwesomeWidget",
  "review": [{
    "@type": "Review",
    "author": { "@type": "Person", "name": "Fred Benson" },
    "datePublished": "2024-03-15",
    "reviewBody": "Great widget, works as advertised.",
    "reviewRating": { "@type": "Rating", "ratingValue": 4, "bestRating": 5 }
  }],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": 4.4,
    "reviewCount": 89,
    "bestRating": 5
  }
}
```

**Important:** Google ignores self-serving reviews (an organization reviewing itself or its own products). Reviews should come from genuine third parties.

---

## 22. SoftwareApplication

**Required:** `name`, and one of `aggregateRating`/`review`, plus `offers`
**Recommended:** `operatingSystem`, `applicationCategory`

```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Angry Birds",
  "operatingSystem": "ANDROID, IOS",
  "applicationCategory": "GameApplication",
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": 4.6,
    "ratingCount": 8864
  },
  "offers": {
    "@type": "Offer",
    "price": 1.00,
    "priceCurrency": "USD"
  }
}
```

Co-type for specific categories:
```json
"@type": ["SoftwareApplication", "MobileApplication"]
```

For a free app, use `"price": "0"` — don't omit `offers`.

---

## 23. Speakable

⚠️ Only supported for Google News publishers, primarily in the US. Use sparingly.

```json
{
  "@context": "https://schema.org/",
  "@type": "NewsArticle",
  "headline": "Article Title",
  "url": "https://www.example.com/article",
  "speakable": {
    "@type": "SpeakableSpecification",
    "cssSelector": [".headline", ".summary"]
  }
}
```

---

## 24. Subscription / Paywalled Content

Add these fields to whatever page type the content is (usually `NewsArticle` or `Article`):

```json
{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "mainEntityOfPage": { "@type": "WebPage", "@id": "https://example.com/article" },
  "headline": "Article Headline",
  "datePublished": "2024-02-05T08:00:00+08:00",
  "author": { "@type": "Person", "name": "Jane Doe" },
  "isAccessibleForFree": false,
  "hasPart": [
    { "@type": "WebPageElement", "isAccessibleForFree": false, "cssSelector": ".paywall" }
  ]
}
```

Multiple paywalled sections → multiple entries in the `hasPart` array with different `cssSelector` values.

---

## 25. VacationRental

⚠️ **Requires Google partnership (Hotel Center access + Technical Account Manager).** Markup without the partnership does nothing for rich results.

```json
{
  "@context": "https://schema.org",
  "@type": "VacationRental",
  "name": "Sunny Beach Cottage",
  "description": "Two-bedroom cottage on Malibu beach with ocean views and a private deck.",
  "image": [
    "https://example.com/photos/1.jpg",
    "https://example.com/photos/2.jpg",
    "https://example.com/photos/3.jpg",
    "https://example.com/photos/4.jpg",
    "https://example.com/photos/5.jpg",
    "https://example.com/photos/6.jpg",
    "https://example.com/photos/7.jpg",
    "https://example.com/photos/8.jpg"
  ],
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Ocean View Dr",
    "addressLocality": "Malibu",
    "addressRegion": "CA",
    "postalCode": "90265",
    "addressCountry": "US"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 34.025922,
    "longitude": -118.779757
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": 4.8,
    "ratingCount": 120
  },
  "containsPlace": {
    "@type": "Accommodation",
    "additionalType": "https://schema.org/House",
    "numberOfBedrooms": 2,
    "numberOfBathroomsTotal": 1,
    "occupancy": { "@type": "QuantitativeValue", "value": 4 },
    "amenityFeature": [
      { "@type": "LocationFeatureSpecification", "name": "wifi", "value": true },
      { "@type": "LocationFeatureSpecification", "name": "kitchen", "value": true },
      { "@type": "LocationFeatureSpecification", "name": "pool", "value": false }
    ]
  }
}
```

---

## 26. VideoObject

**Required:** `name`, `description`, `thumbnailUrl`, `uploadDate`
**Recommended:** `duration`, `contentUrl`, `embedUrl`

```json
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "How to Make Peanut Butter Cookies",
  "description": "A quick video demonstrating how to make peanut butter cookies.",
  "thumbnailUrl": [
    "https://example.com/thumbnails/1x1.jpg",
    "https://example.com/thumbnails/4x3.jpg",
    "https://example.com/thumbnails/16x9.jpg"
  ],
  "uploadDate": "2024-02-05T08:00:00+08:00",
  "duration": "PT1M33S",
  "contentUrl": "https://example.com/video.mp4",
  "embedUrl": "https://example.com/embed/video",
  "interactionStatistic": {
    "@type": "InteractionCounter",
    "interactionType": { "@type": "WatchAction" },
    "userInteractionCount": 2347
  }
}
```

**With chapters (Clip):**
```json
"hasPart": [
  { "@type": "Clip", "name": "Intro", "startOffset": 0, "endOffset": 30, "url": "https://example.com/video?t=0" },
  { "@type": "Clip", "name": "Mixing", "startOffset": 30, "endOffset": 90, "url": "https://example.com/video?t=30" },
  { "@type": "Clip", "name": "Baking", "startOffset": 90, "endOffset": 180, "url": "https://example.com/video?t=90" }
]
```

**With deep-linking (SeekToAction):**
```json
"potentialAction": {
  "@type": "SeekToAction",
  "target": "https://example.com/video?t={seek_to_second_number}",
  "startOffset-input": "required name=seek_to_second_number"
}
```

**For livestreams (LIVE badge):**
```json
"publication": {
  "@type": "BroadcastEvent",
  "isLiveBroadcast": true,
  "startDate": "2024-10-27T14:00:00-07:00",
  "endDate": "2024-10-27T15:00:00-07:00"
}
```

---

## 27. WebSite with SearchAction

Unlocks the sitelinks searchbox in Google Search. Place on the homepage.

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Example Site",
  "url": "https://www.example.com/",
  "potentialAction": {
    "@type": "SearchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "https://www.example.com/search?q={search_term_string}"
    },
    "query-input": "required name=search_term_string"
  }
}
```

---

## Combining schemas on one page

Two patterns, both valid:

**Pattern A — separate script tags:**
```html
<script type="application/ld+json">{...Article...}</script>
<script type="application/ld+json">{...BreadcrumbList...}</script>
<script type="application/ld+json">{...Organization...}</script>
```

**Pattern B — @graph array in one script:**
```json
{
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "Article", "..." : "..." },
    { "@type": "BreadcrumbList", "..." : "..." },
    { "@type": "Organization", "..." : "..." }
  ]
}
```

Separate scripts are easier to maintain and debug; `@graph` is more compact. Either way Google parses them correctly.
