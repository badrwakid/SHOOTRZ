# Gemini Future Improvements

Potential enhancements to the Gemini integration layer, ordered by impact.

---

## 1. Response Caching

**Impact**: High (cost reduction, latency improvement)

- Cache structured outputs (shot feedback, drill explanations) by input hash
- Use Redis or in-memory TTL cache for repeated queries
- Chat responses should NOT be cached (contextual and unique)
- Estimated savings: 60-70% reduction in Gemini API calls for recurring analysis patterns

## 2. Prompt Versioning

**Impact**: High (quality control, A/B testing)

- Version prompt templates with semantic versioning (e.g., `shot_feedback_v1.2`)
- Store prompt versions in a config file or database
- Log which prompt version generated each response
- Enable rollback to previous versions if quality degrades
- Track output quality metrics per prompt version

## 3. A/B Testing Framework

**Impact**: Medium-High (quality optimization)

- Route a percentage of requests to experimental prompts
- Collect user feedback signals (thumbs up/down, engagement metrics)
- Compare Gemini-generated vs. rule-based feedback quality
- Measure: response relevance, user engagement, session return rate

## 4. Multimodal Input (Video Frames)

**Impact**: Medium (enhanced analysis)

- Pass key frame images directly to Gemini along with metric data
- Enable visual analysis: "Your elbow is here — see the angle?"
- Requires Gemini Pro Vision or equivalent multimodal model
- Would significantly enhance coaching quality with visual context

## 5. RAG (Retrieval-Augmented Generation)

**Impact**: Medium (coaching depth)

- Build a knowledge base of basketball coaching literature
- Index scientific papers (Cabarkapa et al., etc.) and coaching manuals
- Retrieve relevant passages to include in prompts
- Enables more specific, citation-backed coaching advice

## 6. Streaming Structured Output

**Impact**: Medium (UX improvement)

- Currently structured outputs are batch-only
- Streaming structured output would allow progressive UI rendering
- The google-genai SDK may support this in future versions

## 7. Fine-Tuned Model

**Impact**: Medium-High (quality, latency)

- Fine-tune Gemini on SHOOTRZ-specific coaching data
- Train on high-quality coach feedback examples
- Would reduce prompt size and improve consistency
- Requires significant labeled data collection

## 8. Token Usage Analytics

**Impact**: Low-Medium (cost management)

- Track token usage per feature area (chat, feedback, drills, etc.)
- Set alerts for unusual consumption spikes
- Dashboard for token budget monitoring
- The `usage_metadata` is already extracted in `gemini_client.py`

## 9. Multi-Language Support

**Impact**: Medium (accessibility)

- Add locale parameter to prompt builders
- Instruct Gemini to respond in the user's language
- Requires translation of prompt templates
- i18n already exists in the mobile app via `react-i18next`

## 10. Confidence-Gated LLM Calls

**Impact**: Low-Medium (efficiency)

- Skip Gemini enrichment when all metrics have high confidence and "Good" verdicts
- Only call LLM when there's meaningful coaching content to generate
- Reduces unnecessary API calls for obvious results

## 11. Batch Processing

**Impact**: Low (efficiency for bulk analysis)

- Support batch analysis of multiple shots in a single Gemini call
- Useful for session-level analysis with multiple recordings
- Reduces API call count and latency

## 12. Safety and Content Filtering

**Impact**: Low (already handled)

- The Coach J persona naturally constrains output to basketball coaching
- Add explicit content safety checks for edge cases
- Monitor for off-topic or harmful responses
- Current implementation already guards against hallucination via data grounding
