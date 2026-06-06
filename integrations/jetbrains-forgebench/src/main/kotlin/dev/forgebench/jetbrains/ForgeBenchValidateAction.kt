package dev.forgebench.jetbrains

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.ui.Messages

class ForgeBenchValidateAction : AnAction() {
    override fun actionPerformed(event: AnActionEvent) {
        val project = event.project ?: return
        val base = project.basePath ?: "."
        val guardrails = ForgeBenchSettings.getInstance().state.guardrailsFile
        val result = ForgeBenchCli.run(
            project,
            listOf("validate", "--repo", base, "--file", guardrails, "--strict"),
        )
        if (result.exitCode != 0) {
            Messages.showErrorDialog(project, result.output, "ForgeBench validate failed")
            return
        }
        Messages.showInfoMessage(project, "Guardrails validated.", "ForgeBench")
    }
}