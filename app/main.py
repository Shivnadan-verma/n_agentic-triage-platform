# AI assisted development
"""
Main entry point for Agentic Triage Platform.

ADK Usage:
- SupervisorAgent inherits from google.adk.Agent (ADK)
- Uses ADK's run(input, state) method signature
- ADK provides agent structure and lifecycle

Manual Calls (Not using ADK's sub_agents):
- Currently calling BugAnalysisAgent and AssignmentAgent manually
- Could use ADK's sub_agents and find_sub_agent() instead
- Manual calls are simpler for this use case
"""
import json
from app.agents.supervisor.agent import SupervisorAgent
from app.agents.bug_analysis.agent import BugAnalysisAgent
from app.agents.assignment.agent import AssignmentAgent

def main():
    print("=" * 60)
    print("Agentic Triage Platform - Multiple Bug Analysis")
    print("=" * 60)
    
    # ============================================================
    # ADK USAGE: SupervisorAgent is an ADK Agent
    # ============================================================
    supervisor = SupervisorAgent()
    analyzer = BugAnalysisAgent()
    assigner = AssignmentAgent()
    
    # Load multiple bugs
    print("\n[Input] Loading bugs from data folder...")
    with open("app/data/input/bugs.json", "r") as f:
        bugs = json.load(f)
    
    with open("app/data/input/engineer.json", "r") as f:
        engineers = json.load(f)
    
    print(f"Found {len(bugs)} bugs to process\n")
    
    # Process each bug
    all_results = []
    
    for idx, bug in enumerate(bugs, 1):
        print("=" * 60)
        print(f"Processing Bug {idx}/{len(bugs)}: {bug['bug_id']}")
        print("=" * 60)
        
        # ============================================================
        # ADK USAGE: Supervisor Agent
        # ============================================================
        sup_result, _ = supervisor.run(bug)
        
        print(f"\n[1] Bug Data:")
        print(f"   Bug ID: {sup_result['bug']['bug_id']}")
        print(f"   Severity: {sup_result['bug']['severity']}")
        print(f"   Product: {sup_result['bug']['product']}")
        print(f"   Description: {sup_result['bug']['description']}")
        print(f"   Routes: {sup_result['routes']}")
        
        # ============================================================
        # MANUAL CALL: Bug Analysis Agent
        # ============================================================
        analysis_result, _ = analyzer.run(sup_result['bug'])
        print(f"\n[2] Bug Analysis:")
        print(f"   Impact Score: {analysis_result['impact_score']}")
        
        # ============================================================
        # MANUAL CALL: Assignment Agent
        # ============================================================
        assignment_result, _ = assigner.run({
            "bug": sup_result['bug'],
            "engineers": engineers
        })
        
        assigned_engineer = next(
            (e for e in engineers if e['ldap_id'] == assignment_result['assigned_to']), 
            None
        )
        
        print(f"\n[3] Assignment:")
        print(f"   Assigned to: {assignment_result['assigned_to']}")
        if assigned_engineer:
            print(f"   Engineer: {assigned_engineer['name']} ({assigned_engineer['role']})")
            print(f"   Skills: {', '.join(assigned_engineer['skill_set'])}")
            print(f"   Product: {assigned_engineer['product']}")
            print(f"   Rating: {assigned_engineer['rating']}")
            print(f"   Workload: {assigned_engineer['total_no_of_bugs']} bugs")
        
        # Store results
        all_results.append({
            "bug": sup_result['bug'],
            "analysis": analysis_result,
            "assignment": assignment_result,
            "engineer": assigned_engineer
        })
        
        print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY - All Bugs Processed")
    print("=" * 60)
    print(f"\nTotal Bugs: {len(all_results)}")
    print(f"\nBreakdown by Severity:")
    severity_count = {}
    for r in all_results:
        sev = r['bug']['severity']
        severity_count[sev] = severity_count.get(sev, 0) + 1
    for sev, count in sorted(severity_count.items()):
        print(f"  {sev}: {count}")
    
    print(f"\nBreakdown by Product:")
    product_count = {}
    for r in all_results:
        prod = r['bug']['product']
        product_count[prod] = product_count.get(prod, 0) + 1
    for prod, count in sorted(product_count.items()):
        print(f"  {prod}: {count}")
    
    print(f"\nBreakdown by Impact Score:")
    high_impact = sum(1 for r in all_results if r['analysis']['impact_score'] == 80)
    low_impact = sum(1 for r in all_results if r['analysis']['impact_score'] == 40)
    print(f"  High Impact (80): {high_impact}")
    print(f"  Low Impact (40): {low_impact}")
    
    print(f"\nAssignment Summary:")
    engineer_assignments = {}
    for r in all_results:
        eng_id = r['assignment']['assigned_to']
        engineer_assignments[eng_id] = engineer_assignments.get(eng_id, 0) + 1
    for eng_id, count in sorted(engineer_assignments.items()):
        eng = next((e for e in engineers if e['ldap_id'] == eng_id), None)
        eng_name = eng['name'] if eng else eng_id
        print(f"  {eng_name} ({eng_id}): {count} bugs")
    
    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
