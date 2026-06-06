package dev.forgebench.jetbrains

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.ui.Messages

class ForgeBenchPolicyTestAction : AnAction() {
    override fun actionPerformed(event: AnActionEvent) {
        val project = event.project ?: return
        val result = ForgeBenchCli.run(
            project,
            listOf("policy", "test", "--tests", "examples/policy_tests", "--repo", project.basePath ?: "."),
        )
        if (result.exitCode != 0) {
            Messages.showErrorDialog(project, result.output, "ForgeBench policy tests failed")
            return
        }
        Messages.showInfoMessage(project, "ForgeBench policy tests passed.", "ForgeBench")
    }
}