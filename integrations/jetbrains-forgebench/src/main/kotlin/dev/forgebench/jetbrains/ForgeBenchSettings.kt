package dev.forgebench.jetbrains

import com.intellij.openapi.components.PersistentStateComponent
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage
import com.intellij.openapi.components.service

@State(name = "ForgeBenchSettings", storages = [Storage("forgebench.xml")])
class ForgeBenchSettings : PersistentStateComponent<ForgeBenchSettings.State> {
    data class State(
        var guardrailsFile: String = "forgebench.yml",
        var outputDir: String = "forgebench-output",
        var policyTestsDir: String = "examples/policy_tests",
        var runChecks: Boolean = false,
        var showOnboardingOnFirstRun: Boolean = true,
    )

    private var state = State()

    override fun getState(): State = state

    override fun loadState(state: State) {
        this.state = state
    }

    companion object {
        fun getInstance(): ForgeBenchSettings = service()
    }
}