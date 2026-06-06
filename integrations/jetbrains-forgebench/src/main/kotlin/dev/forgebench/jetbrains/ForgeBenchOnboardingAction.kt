package dev.forgebench.jetbrains

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.ui.Messages

class ForgeBenchOnboardingAction : AnAction() {
    override fun actionPerformed(event: AnActionEvent) {
        val project = event.project ?: return
        val base = project.basePath ?: "."
        val steps = arrayOf(
            "doctor" to listOf("doctor", "--repo", base),
            "demo" to listOf("demo", "--repo", base),
            "status" to listOf("status", "--repo", base),
        )
        val choice = Messages.showChooseDialog(
            project,
            "Run the full ForgeBench onboarding checklist (doctor → demo → status)?",
            "ForgeBench Onboarding",
            Messages.getQuestionIcon(),
            arrayOf("Run checklist", "Doctor only", "Cancel"),
            "Run checklist",
        )
        if (choice == 2 || choice < 0) return
        val selected = if (choice == 0) steps else arrayOf(steps[0])
        val output = StringBuilder()
        for ((label, args) in selected) {
            output.append("=== $label ===\n")
            val result = ForgeBenchCli.run(project, args)
            output.append(result.output).append("\n")
            if (result.exitCode != 0 && label == "doctor") {
                Messages.showWarningDialog(project, output.toString(), "ForgeBench onboarding")
                return
            }
        }
        Messages.showInfoMessage(project, output.toString(), "ForgeBench onboarding complete")
    }
}