import os
import click
import glob
import json
from depattern.config import Config
from depattern.scrubber import Scrubber
from depattern.rewriter import Rewriter
from depattern.schema import SchemaGenerator
from depattern.exporter import Exporter
from depattern.providers.gemini import GeminiProvider

def get_color_indicator(val, threshold, lower_is_bad=True):
    if lower_is_bad:
        if val < threshold:
            return f"\033[91m{val} (High Risk - Needs Variance)\033[0m"
        return f"\033[92m{val} (Healthy)\033[0m"
    else:
        if val > threshold:
            return f"\033[91m{val} (High Risk - Over-Patterned)\033[0m"
        return f"\033[92m{val} (Healthy)\033[0m"

@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to custom depattern.toml configuration')
@click.pass_context
def cli(ctx, config):
    """
    depattern: Audit formulaic writing patterns, rewrite drafts, and export schema/slides.
    """
    ctx.ensure_object(dict)
    ctx.obj['config'] = Config(config)

@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--json', 'json_output', is_flag=True, help='Print machine-readable JSON metrics')
@click.option(
    '--max-risk',
    type=click.Choice(['low', 'medium', 'high'], case_sensitive=False),
    help='Exit with code 1 if the pattern risk is above this level'
)
@click.pass_context
def analyze(ctx, filepath, json_output, max_risk):
    """
    Runs an offline, rule-based linguistic audit of the draft document (No-LLM mode).
    """
    config = ctx.obj['config']
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
        
    scrubber = Scrubber(config)
    res = scrubber.analyze(text)
    
    if "error" in res:
        click.echo(f"Error: {res['error']}")
        return

    risk_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    should_fail = False
    if max_risk:
        current = risk_order[res["summary"]["slop_risk"]]
        allowed = risk_order[max_risk.upper()]
        should_fail = current > allowed

    if json_output:
        click.echo(json.dumps(res, indent=2))
        if should_fail:
            raise click.ClickException(
                f"Pattern risk {res['summary']['slop_risk']} exceeds --max-risk {max_risk.upper()}"
            )
        return

    # Visual header
    click.echo("=" * 60)
    click.echo(f"           DEPATTERN LINGUISTIC AUDIT: {os.path.basename(filepath)}")
    click.echo("=" * 60)
    
    risk = res["summary"]["slop_risk"]
    if risk == "HIGH":
        risk_colored = f"\033[91m[HIGH RISK - Formulaic Patterning]\033[0m"
    elif risk == "MEDIUM":
        risk_colored = f"\033[93m[MEDIUM RISK - Mix of Signatures]\033[0m"
    else:
        risk_colored = f"\033[92m[LOW RISK - Natural/Human Rhythm]\033[0m"
        
    click.echo(f"Overall Pattern Risk:   {risk_colored}")
    click.echo(f"Pattern Artifact Score: {res['summary']['pattern_artifact_score']}/9")
    click.echo("-" * 60)
    
    metrics = res["metrics"]
    click.echo("Linguistic Metrics:")
    
    # Variance check
    variance_indicator = get_color_indicator(
        metrics["sentence_length_variance"], 
        config.sentence_length_variance_threshold,
        lower_is_bad=True
    )
    click.echo(f" - Sentence Length StdDev:  {variance_indicator}")
    click.echo(f" - Paragraph Rhythm StdDev: {metrics['paragraph_rhythm_variance']}")
    
    # Banned transition check
    trans_indicator = get_color_indicator(
        metrics["banned_transition_density"] * 100,
        config.banned_transition_density_threshold * 100,
        lower_is_bad=False
    )
    click.echo(f" - Banned Transition %:     {trans_indicator}%")
    click.echo(f" - Abstract Noun %:         {round(metrics['abstract_noun_density'] * 100, 2)}%")
    click.echo(f" - Vague Intensifier Count: {metrics['vague_intensifier_count']}")
    
    # Answer first check
    ans_ok = "\033[92m[OK]\033[0m" if metrics["answer_first_ok"] else "\033[91m[MISSING/OUTSIDE LIMITS]\033[0m"
    click.echo(f" - AEO Answer-First Layout: {ans_ok} ({metrics['answer_first_words']} words, target {config.answer_first_word_count_min}-{config.answer_first_word_count_max})")
    
    details = res["details"]
    if details["banned_phrases_found"] or details["vague_intensifiers_found"] or details["abstract_nouns_found"] or details["repeated_openers"]:
        click.echo("-" * 60)
        click.echo("Linguistic Artifact Details:")
        
        if details["banned_phrases_found"]:
            phrases_str = ", ".join(f"'{p}' (x{c})" for p, c in details["banned_phrases_found"])
            click.echo(f" - Banned transitions: {phrases_str}")
            
        if details["vague_intensifiers_found"]:
            int_str = ", ".join(f"'{p}' (x{c})" for p, c in details["vague_intensifiers_found"])
            click.echo(f" - Vague intensifiers: {int_str}")
            
        if details["abstract_nouns_found"]:
            nouns_str = ", ".join(f"'{p}' (x{c})" for p, c in details["abstract_nouns_found"])
            click.echo(f" - Abstract nouns: {nouns_str}")
            
        if details["repeated_openers"]:
            openers_str = ", ".join(f"'{k}' (x{v})" for k, v in details["repeated_openers"].items())
            click.echo(f" - Repeated openers:   {openers_str}")
            
    click.echo("=" * 60)
    if should_fail:
        raise click.ClickException(
            f"Pattern risk {res['summary']['slop_risk']} exceeds --max-risk {max_risk.upper()}"
        )

@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--json', 'json_output', is_flag=True, help='Print machine-readable JSON suggestions')
@click.pass_context
def suggest(ctx, filepath, json_output):
    """
    Prints offline edit suggestions without calling an LLM provider.
    """
    config = ctx.obj['config']
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    scrubber = Scrubber(config)
    suggestions = scrubber.suggest(text)

    if json_output:
        click.echo(json.dumps({"suggestions": suggestions}, indent=2))
        return

    click.echo("=" * 60)
    click.echo(f"           DEPATTERN EDIT SUGGESTIONS: {os.path.basename(filepath)}")
    click.echo("=" * 60)
    for idx, item in enumerate(suggestions, 1):
        severity = item["severity"].upper()
        click.echo(f"{idx}. [{severity}] {item['title']}")
        click.echo(f"   {item['detail']}")
    click.echo("=" * 60)

@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--out', '-o', type=click.Path(), help='File to write rewritten content to')
@click.option('--diff', '-d', is_flag=True, help='Print colored unified diff of changes')
@click.option('--voice', '-v', help='Override default brand voice prompt instruction')
@click.option('--answer-first', '-a', is_flag=True, help='Generate an AEO-ready direct summary at the start')
@click.pass_context
def process(ctx, filepath, out, diff, voice, answer_first):
    """
    Rewrites content using the configured LLM to reduce formulaic patterns and improve clarity.
    """
    config = ctx.obj['config']
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
        
    try:
        provider = GeminiProvider(config)
        rewriter = Rewriter(config, provider)
        
        click.echo(f"Contacting Gemini provider ({config.llm_model})...", err=True)
        processed = rewriter.process(text, voice=voice, answer_first=answer_first)
        
        if diff:
            diff_output = rewriter.get_diff(text, processed)
            click.echo("\n--- VISUAL DIFF HIGHLIGHTS ---")
            click.echo(diff_output)
            click.echo("------------------------------\n")
            
        if out:
            with open(out, 'w', encoding='utf-8') as f:
                f.write(processed)
            click.echo(f"Successfully processed. Written output to: {out}")
        elif not diff:
            # Output directly to stdout if no out path is given and diff isn't requested
            click.echo(processed)
            
    except Exception as e:
        click.echo(f"\033[91mError running rewrite: {e}\033[0m", err=True)
        raise click.Abort()

@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--type', '-t', 'schema_type', required=True, type=click.Choice(['LocalBusiness', 'Person', 'Article', 'FAQPage'], case_sensitive=False), help='Type of schema profile to generate')
@click.option('--out', '-o', type=click.Path(), help='File path to write schema output to')
@click.pass_context
def schema(ctx, filepath, schema_type, out):
    """
    Extracts metadata from draft and compiles a compliant JSON-LD graph.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
        
    generator = SchemaGenerator()
    result = generator.generate(text, schema_type)
    
    formatted = json.dumps(result, indent=2)
    
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(formatted)
        click.echo(f"Successfully exported {schema_type} schema to: {out}")
    else:
        click.echo(formatted)

@cli.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--out', '-o', type=click.Path(), help='File path to write Marp slides to')
@click.option('--use-llm', is_flag=True, help='Use LLM provider to draft content slides (requires GEMINI_API_KEY)')
@click.pass_context
def slides(ctx, filepath, out, use_llm):
    """
    Converts strategy text into Marp-compatible markdown presentation slides.
    """
    config = ctx.obj['config']
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
        
    provider = None
    if use_llm:
        try:
            provider = GeminiProvider(config)
        except Exception as e:
            click.echo(f"Warning: Failed to setup LLM provider: {e}. Falling back to offline generation.", err=True)
            
    exporter = Exporter(config, provider)
    slide_md = exporter.generate_slides(text)
    
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(slide_md)
        click.echo(f"Successfully generated Marp slide deck: {out}")
    else:
        click.echo(slide_md)

@cli.command()
@click.argument('indir', type=click.Path(exists=True, file_okay=False))
@click.option('--out', '-o', required=True, type=click.Path(file_okay=False), help='Directory to write polished drafts to')
@click.option('--voice', '-v', help='Override default brand voice instruction')
@click.option('--answer-first', '-a', is_flag=True, help='Generate answer-first segments')
@click.pass_context
def batch(ctx, indir, out, voice, answer_first):
    """
    Processes all markdown files (*.md) in a directory in batch.
    """
    config = ctx.obj['config']
    
    os.makedirs(out, exist_ok=True)
    md_files = glob.glob(os.path.join(indir, "*.md"))
    
    if not md_files:
        click.echo(f"No markdown files found in input directory: {indir}")
        return
        
    click.echo(f"Found {len(md_files)} markdown files in {indir}. Processing batch...", err=True)
    
    try:
        provider = GeminiProvider(config)
        rewriter = Rewriter(config, provider)
        
        for idx, filepath in enumerate(md_files, 1):
            filename = os.path.basename(filepath)
            outpath = os.path.join(out, filename)
            
            click.echo(f"[{idx}/{len(md_files)}] Processing {filename} -> {outpath}...", err=True)
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
                
            processed = rewriter.process(text, voice=voice, answer_first=answer_first)
            with open(outpath, 'w', encoding='utf-8') as f:
                f.write(processed)
                
        click.echo(f"Batch processing completed. Polished drafts saved in: {out}")
        
    except Exception as e:
        click.echo(f"\033[91mError running batch process: {e}\033[0m", err=True)
        raise click.Abort()

if __name__ == '__main__':
    cli()
