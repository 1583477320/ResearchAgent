import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.workflow.research_workflow import ResearchWorkflow


def main():
    topic = input("Enter research topic: ").strip()
    
    if not topic:
        topic = "Agent Memory"
    
    full_analysis = input("Include full analysis? (y/N): ").strip().lower() == "y"
    
    workflow = ResearchWorkflow(include_full_analysis=full_analysis)
    
    try:
        print(f"\nStarting research on: {topic}")
        print(f"Full analysis mode: {'Yes' if full_analysis else 'No'}")
        print("=" * 60)
        
        package = workflow.run(topic, max_papers=10)
        
        # 创建输出目录
        output_dir = f"research_package_{topic.replace(' ', '_')[:20]}"
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存所有文件
        for filename, content in package.items():
            file_path = os.path.join(output_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Saved: {filename}")
        
        print("\n" + "=" * 60)
        print(f"Research completed! Package saved to: {output_dir}")
        print("\nFiles generated:")
        for filename in package.keys():
            print(f"  - {filename}")
        
        # 预览最终报告
        if "final_report.md" in package:
            print("\n" + "=" * 60)
            print("Preview of final_report.md:")
            print("-" * 60)
            preview = package["final_report.md"]
            print(preview[:2000])
            if len(preview) > 2000:
                print("\n... (truncated)")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
