import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.workflow.research_workflow import ResearchWorkflow


def main():
    topic = input("Enter research topic: ").strip()
    if not topic:
        topic = "Agent Memory"

    workflow = ResearchWorkflow()

    try:
        print(f"\nStarting research on: {topic}")
        print("=" * 60)

        package = workflow.run(topic, max_papers=10)

        output_dir = f"research_package_{topic.replace(' ', '_')[:20]}"
        os.makedirs(output_dir, exist_ok=True)

        for filename, content in package.items():
            file_path = os.path.join(output_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Saved: {filename}")

        print("\n" + "=" * 60)
        print(f"Research completed! Package saved to: {output_dir}")

    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
