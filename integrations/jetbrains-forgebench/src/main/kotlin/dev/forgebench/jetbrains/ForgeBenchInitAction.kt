package dev.forgebench.jetbrains

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.ui.Messages

class ForgeBenchInitAction : AnAction() {
    override fun actionPerformed(event: AnActionEvent) {
        val project = event.project ?: return
        val base = project.basePath ?: "."
        val enterprise = Messages.showYesNoDialog(
            project,
            "Generate enterprise starter kit (org policy, CI, onboarding docs)?",
            "ForgeBench Init",
            Messages.getQuestionIcon(),
        )
        val args = if (enterprise == Messages.YES) {
            listOf("init", "--enterprise", "--yes", "--repo", base)
        } else {
            listOf("init", "--repo", base, "--out", ForgeBenchSettings.getInstance().state.guardrailsFile)
        }
        val result = ForgeBenchCli.run(project, args)
        if (result.exitCode != 0) {
            Messages.showErrorDialog(project, result.output, "ForgeBench init failed")
            return
        }
        Messages.showInfoMessage(project, result.output, "ForgeBench init complete")
    }
}